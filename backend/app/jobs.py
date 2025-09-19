from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .seeds import seed_slots_for_day, generate_recommendations

def generate_for_date(db: Session, target_date: datetime | None = None) -> str:
    d = target_date or (datetime.now() + timedelta(days=1))
    seed_slots_for_day(db, d)
    generate_recommendations(db, d)
    return d.date().isoformat()
