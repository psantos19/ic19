from datetime import date as date_cls, datetime, timedelta
from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .db import Base, engine, get_db
from . import models, schemas
from .jobs import generate_for_date

app = FastAPI(title="IC19 API", version="0.1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # afina se precisares
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def init_db():
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/signup")
def signup(payload: schemas.SignupIn, db: Session = Depends(get_db)):
    emp = None
    if payload.employer_name:
        emp = db.query(models.Employer).filter_by(name=payload.employer_name).first()
        if not emp:
            emp = models.Employer(name=payload.employer_name)
            db.add(emp)
            db.flush()

    u = models.User(
        employer_id = emp.id if emp else None,
        home_zone = payload.home_zone,
        work_zone = payload.work_zone,
        flex_minus_min = payload.flex_minus_min,
        flex_plus_min  = payload.flex_plus_min,
        preferences_json = {},
        # quota semanal inicial (ex.: 2) se vier a zero na BD
        nudge_quota_week = 2
    )
    db.add(u)
    db.commit()

    # gerar recomendações para amanhã (regera para toda a base; simples para MVP)
    generate_for_date(db)

    return {"user_id": u.id}

@app.get("/recommendations/{user_id}")
def get_recs(user_id: int, date_str: str, db: Session = Depends(get_db)):
    recs = (db.query(models.Recommendation)
              .filter_by(user_id=user_id, date=date_cls.fromisoformat(date_str))
              .order_by(models.Recommendation.alt_rank)
              .all())
    return [
        {"slot_iso": r.slot_iso, "eta_min": r.predicted_eta_min, "rank": r.alt_rank, "chosen": r.chosen_bool}
        for r in recs
    ]

@app.post("/accept")
def accept(body: schemas.AcceptIn, db: Session = Depends(get_db)):
    rec = (db.query(models.Recommendation)
             .filter_by(user_id=body.user_id, date=date_cls.fromisoformat(body.date), slot_iso=body.slot_iso)
             .first())
    if rec:
        rec.chosen_bool = True
        db.commit()
        return {"accepted": True}
    return {"accepted": False, "reason": "Recommendation not found"}

@app.post("/admin/generate")
def admin_generate(date_str: str | None = Query(None, description="YYYY-MM-DD"), db: Session = Depends(get_db)):
    target_dt = None
    if date_str:
        target_dt = datetime.fromisoformat(date_str)
    out = generate_for_date(db, target_dt)
    return {"generated_for": out}
