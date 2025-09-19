from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from .db import Base

class Employer(Base):
    __tablename__ = "employers"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    employer_id = Column(Integer, ForeignKey("employers.id"), nullable=True)
    home_zone = Column(String, nullable=False)   # ex: "Sintra-Noroeste"
    work_zone = Column(String, nullable=False)   # ex: "Lisboa-Centro"
    flex_minus_min = Column(Integer, default=0)
    flex_plus_min  = Column(Integer, default=0)
    preferences_json = Column(JSON, default={})
    fairness_score = Column(Integer, default=0)
    nudge_quota_week = Column(Integer, default=2)

class Slot(Base):
    __tablename__ = "slots"
    id = Column(Integer, primary_key=True)
    date = Column(Date, index=True)
    bin_start_iso = Column(String, index=True)  # ISO do início do bin (5 min)
    capacity_estimate = Column(Integer, nullable=False)
    allocated_count = Column(Integer, default=0)
    __table_args__ = (UniqueConstraint("date", "bin_start_iso", name="uix_slot_date_bin"),)

class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    date = Column(Date, index=True)
    slot_iso = Column(String)
    predicted_eta_min = Column(Integer)
    alt_rank = Column(Integer)       # 1, 2, 3...
    chosen_bool = Column(Boolean, default=False)

class Nudge(Base):
    __tablename__ = "nudges"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    date = Column(Date, index=True)
    from_slot_iso = Column(String)
    to_slot_iso = Column(String)
    reward_points = Column(Integer, default=0)
    accepted_bool = Column(Boolean, default=False)

class Trip(Base):
    __tablename__ = "trips"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    depart_ts = Column(DateTime)
    arrive_ts = Column(DateTime)
    realized_eta_min = Column(Integer)
    verification_flags = Column(JSON, default={})
