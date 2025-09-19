const KEY = "ic19_user_id";

export function saveUserId(id: number) {
  try { localStorage.setItem(KEY, String(id)); } catch {}
}

export function getUserId(): number | null {
  try {
    const v = localStorage.getItem(KEY);
    return v ? Number(v) : null;
  } catch {
    return null;
  }
}

export function clearUserId() {
  try { localStorage.removeItem(KEY); } catch {}
}
