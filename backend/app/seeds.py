import os
from datetime import datetime, timedelta, time
from sqlalchemy.orm import Session
from .db import engine, SessionLocal, Base
from . import models
from .allocator import greedy_allocate
from .config import capacity_for_datetime, load_capacity_config

# Config
BINS_MIN = 5
AM_START = time(7, 30)
AM_END   = time(10, 30)
PM_START = time(16, 0)
PM_END   = time(20, 0)

def daterange_bins(d: datetime, start: time, end: time, step_min: int):
    cur = datetime.combine(d.date(), start)
    end_dt = datetime.combine(d.date(), end)
    while cur <= end_dt:
        yield cur
        cur += timedelta(minutes=step_min)

def eta_heuristic(bin_dt: datetime) -> int:
    """ Heurística simples para ETA (min) consoante a hora do dia. """
    h = bin_dt.hour + bin_dt.minute/60
    base = 28
    if 8.0 <= h <= 9.0: return int(base * 1.6)
    if 7.5 <= h < 8.0 or 9.0 < h <= 9.5: return int(base * 1.35)
    if 17.0 <= h <= 18.0: return int(base * 1.5)
    if 16.0 <= h < 17.0 or 18.0 < h <= 19.0: return int(base * 1.25)
    return int(base * 1.05)

def seed_users(db: Session):
    if db.query(models.User).count() > 0:
        return
    users = [
        ("Sintra-Noroeste", "Lisboa-Centro", 10, 20),
        ("Sintra-Sul", "Lisboa-Centro", 15, 15),
        ("Queluz-Massamá", "Lisboa-Centro", 0, 30),
        ("Amadora-Norte", "Lisboa-Centro", 5, 10),
        ("Sintra-Nascente", "Lisboa-Centro", 10, 10),
        ("Mem Martins", "Lisboa-Centro", 0, 20),
        ("Rio de Mouro", "Lisboa-Centro", 5, 15),
        ("Cacém", "Lisboa-Centro", 20, 10),
        ("Belas", "Lisboa-Centro", 10, 10),
        ("Algueirão", "Lisboa-Centro", 15, 15),
    ]
    for hz, wz, fminus, fplus in users:
        u = models.User(home_zone=hz, work_zone=wz, flex_minus_min=fminus, flex_plus_min=fplus)
        db.add(u)
    db.commit()

def seed_slots_for_day(db: Session, d: datetime):
    rules = load_capacity_config()
    date_only = d.date()
    if db.query(models.Slot).filter_by(date=date_only).count() > 0:
        return

    # manhã
    for bin_dt in daterange_bins(d, AM_START, AM_END, BINS_MIN):
        cap = capacity_for_datetime(bin_dt, rules)
        db.add(models.Slot(date=date_only, bin_start_iso=bin_dt.isoformat(),
                           capacity_estimate=cap, allocated_count=0))
    # tarde
    for bin_dt in daterange_bins(d, PM_START, PM_END, BINS_MIN):
        cap = capacity_for_datetime(bin_dt, rules)
        db.add(models.Slot(date=date_only, bin_start_iso=bin_dt.isoformat(),
                           capacity_estimate=cap, allocated_count=0))
    db.commit()

def _top_k_spaced(scored: list[tuple[str,int]], k=3, min_gap_min=10) -> list[str]:
    scored.sort(key=lambda x: x[1])
    top: list[str] = []
    for slot_iso, _eta in scored:
        slot_dt = datetime.fromisoformat(slot_iso)
        if all(abs((slot_dt - datetime.fromisoformat(t)).total_seconds()) >= min_gap_min*60 for t in top):
            top.append(slot_iso)
        if len(top) >= k:
            break
    return top

def generate_recommendations(db: Session, d: datetime):
    date_only = d.date()
    users = db.query(models.User).all()
    slots = db.query(models.Slot).filter_by(date=date_only).all()

    cap_by_slot = {s.bin_start_iso: s.capacity_estimate for s in slots}

    # separar slots manhã/tarde
    am_slots = [s for s in slots if AM_START <= datetime.fromisoformat(s.bin_start_iso).time() <= AM_END]
    pm_slots = [s for s in slots if PM_START <= datetime.fromisoformat(s.bin_start_iso).time() <= PM_END]

    # --- MANHÃ ---
    user_alts_am: dict[int, list[str]] = {}
    demand_by_slot_am: dict[str, list[int]] = {}

    for u in users:
        scored = [(s.bin_start_iso, eta_heuristic(datetime.fromisoformat(s.bin_start_iso))) for s in am_slots]
        alts = _top_k_spaced(scored, k=3, min_gap_min=10) or [scored[0][0]]
        user_alts_am[u.id] = alts
        demand_by_slot_am.setdefault(alts[0], []).append(u.id)

    assignment_am = greedy_allocate(
        demand_by_slot_am, cap_by_slot, user_alts_am,
        movable_users={u.id for u in users if (u.nudge_quota_week or 0) > 0},
        priority_order=[u.id for u in sorted(users, key=lambda x: (x.fairness_score, -x.nudge_quota_week))]
    )

    # --- TARDE ---
    user_alts_pm: dict[int, list[str]] = {}
    demand_by_slot_pm: dict[str, list[int]] = {}

    for u in users:
        scored = [(s.bin_start_iso, eta_heuristic(datetime.fromisoformat(s.bin_start_iso))) for s in pm_slots]
        if not scored:
            continue
        alts = _top_k_spaced(scored, k=3, min_gap_min=10) or [scored[0][0]]
        user_alts_pm[u.id] = alts
        demand_by_slot_pm.setdefault(alts[0], []).append(u.id)

    assignment_pm = greedy_allocate(
        demand_by_slot_pm, cap_by_slot, user_alts_pm,
        movable_users={u.id for u in users if (u.nudge_quota_week or 0) > 0},
        priority_order=[u.id for u in sorted(users, key=lambda x: (x.fairness_score, -x.nudge_quota_week))]
    )

    # limpar recs do dia e gravar todas
    db.query(models.Recommendation).filter_by(date=date_only).delete()

    moved_users = set()

    # gravar manhã
    for u in users:
        alts = user_alts_am.get(u.id, [])
        assigned = assignment_am.get(u.id, alts[0] if alts else None)
        for rank, slot_iso in enumerate(alts, start=1):
            eta = eta_heuristic(datetime.fromisoformat(slot_iso))
            db.add(models.Recommendation(
                user_id=u.id, date=date_only, slot_iso=slot_iso,
                predicted_eta_min=eta, alt_rank=rank,
                chosen_bool=(assigned == slot_iso and rank == 1)
            ))
        if alts and assigned and assigned != alts[0]:
            moved_users.add(u.id)

    # gravar tarde
    for u in users:
        alts = user_alts_pm.get(u.id, [])
        if not alts:
            continue
        assigned = assignment_pm.get(u.id, alts[0])
        for rank, slot_iso in enumerate(alts, start=1):
            eta = eta_heuristic(datetime.fromisoformat(slot_iso))
            db.add(models.Recommendation(
                user_id=u.id, date=date_only, slot_iso=slot_iso,
                predicted_eta_min=eta, alt_rank=rank,
                chosen_bool=(assigned == slot_iso and rank == 1)
            ))
        if alts and assigned and assigned != alts[0]:
            moved_users.add(u.id)

    db.commit()

    # fairness minimal
    if moved_users:
        for u in db.query(models.User).filter(models.User.id.in_(moved_users)).all():
            u.fairness_score = (u.fairness_score or 0) + 1
            if (u.nudge_quota_week or 0) > 0:
                u.nudge_quota_week -= 1
        db.commit()

def main():
    print("[IC19] Seeds a iniciar…")
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_users(db)
        tomorrow = datetime.now() + timedelta(days=1)
        seed_slots_for_day(db, tomorrow)
        generate_recommendations(db, tomorrow)
    print("[IC19] Seeds concluído.")

if __name__ == "__main__":
    main()
