import json
import os
from datetime import time, datetime

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "config")
CAPACITY_FILE = os.path.join(CONFIG_DIR, "capacity.json")

def load_capacity_config():
    """
    Lê regras de capacidade por intervalos horários.
    Formato em capacity.json (exemplo abaixo).
    """
    if not os.path.exists(CAPACITY_FILE):
        # fallback seguro
        return [
            {"start": "07:30", "end": "10:30", "capacity": 340},
            {"start": "16:00", "end": "20:00", "capacity": 340},
            {"start": "00:00", "end": "23:59", "capacity": 420}
        ]
    with open(CAPACITY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _to_time(hhmm: str) -> time:
    h, m = map(int, hhmm.split(":"))
    return time(h, m)

def capacity_for_datetime(dt: datetime, rules=None) -> int:
    rules = rules or load_capacity_config()
    t = dt.time()
    for r in rules:
        start = _to_time(r["start"])
        end = _to_time(r["end"])
        if start <= t <= end:
            return int(r["capacity"])
    # se nenhuma regra for encontrada, default razoável
    return 420
