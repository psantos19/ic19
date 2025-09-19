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

    for bin_dt in list(daterange_bins(d, AM_START, AM_END, BINS_MIN)) + \
                  list(daterange_bins(d, PM_START, PM_END, BINS_MIN)):
        cap = capacity_for_datetime(bin_dt, rules)
        s = models.Slot(
            date=date_only,
            bin_start_iso=bin_dt.isoformat(),
            capacity_estimate=cap,
            allocated_count=0
        )
        db.add(s)
    db.commit()

def generate_recommendations(db: Session, d: datetime):
    date_only = d.date()
    users = db.query(models.User).all()
    slots = db.query(models.Slot).filter_by(date=date_only).all()

    cap_by_slot = {s.bin_start_iso: s.capacity_estimate for s in slots}

    # alternativas por utilizador
    user_alts: dict[int, list[str]] = {}
    demand_by_slot: dict[str, list[int]] = {}

    # construir candidatos (manhã apenas para já)
    am_slots = [s for s in slots if AM_START <= datetime.fromisoformat(s.bin_start_iso).time() <= AM_END]

    for u in users:
        scored = []
        for s in am_slots:
            bin_dt = datetime.fromisoformat(s.bin_start_iso)
            eta = eta_heuristic(bin_dt)
            scored.append((s.bin_start_iso, eta))
        scored.sort(key=lambda x: x[1])

        # escolher 3 slots espaçados >=10 min
        top = []
        for slot_iso, _eta in scored:
            slot_dt = datetime.fromisoformat(slot_iso)
            if all(abs((slot_dt - datetime.fromisoformat(t)).total_seconds()) >= 10*60 for t in top):
                top.append(slot_iso)
            if len(top) >= 3:
                break

        alts = top or [scored[0][0]]
        user_alts[u.id] = alts
        first = alts[0]
        demand_by_slot.setdefault(first, []).append(u.id)

    # fairness simples: só pode ser deslocado quem tem quota > 0
    movable = {u.id for u in users if (u.nudge_quota_week or 0) > 0}
    # prioridade: menor fairness_score primeiro (quem foi menos penalizado)
    priority = [u.id for u in sorted(users, key=lambda x: (x.fairness_score, -x.nudge_quota_week))]

    assignment = greedy_allocate(
        demand_by_slot, cap_by_slot, user_alts,
        movable_users=movable, priority_order=priority
    )

    # limpar recs do dia e regravar
    db.query(models.Recommendation).filter_by(date=date_only).delete()

    # contabilizar deslocações para atualizar fairness/quotas
    moved_users = set()

    for u in users:
        alts = user_alts.get(u.id, [])
        assigned_slot = assignment.get(u.id, alts[0] if alts else None)
        for rank, slot_iso in enumerate(alts, start=1):
            eta = eta_heuristic(datetime.fromisoformat(slot_iso))
            rec = models.Recommendation(
                user_id=u.id,
                date=date_only,
                slot_iso=slot_iso,
                predicted_eta_min=eta,
                alt_rank=rank,
                chosen_bool=(assigned_slot == slot_iso and rank == 1)
            )
            db.add(rec)
        # se foi movido da 1ª preferência, marca para fairness
        if alts and assigned_slot and assigned_slot != alts[0]:
            moved_users.add(u.id)

    db.commit()

    # Atualiza fairness_score (+1) e reduz quota (-1) de quem foi movido
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
        # só para dev: criar users se vazios
        seed_users(db)
        tomorrow = datetime.now() + timedelta(days=1)
        seed_slots_for_day(db, tomorrow)
        generate_recommendations(db, tomorrow)
    print("[IC19] Seeds concluído.")

if __name__ == "__main__":
    main()
