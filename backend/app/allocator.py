from collections import defaultdict
from typing import Dict, List, Set, Optional

def greedy_allocate(
    demand_by_slot: Dict[str, List[int]],
    cap_by_slot: Dict[str, int],
    user_alternatives: Dict[int, List[str]],
    movable_users: Optional[Set[int]] = None,
    priority_order: Optional[List[int]] = None,
) -> Dict[int, str]:
    """
    - Atribui 1ª preferência a todos.
    - Se bin excede capacidade, tenta mover apenas utilizadores em movable_users (se definido).
    - priority_order (opcional): lista de user_ids pela ordem preferida de deslocação (fairness).
    """
    assignment: Dict[int, str] = {}

    # 1) atribuição inicial
    for slot, uids in demand_by_slot.items():
        for uid in uids:
            if uid not in assignment:
                assignment[uid] = slot

    # 2) resolver overloads
    changed = True
    while changed:
        changed = False
        load = defaultdict(int)
        for s in assignment.values():
            load[s] += 1

        for slot, count in list(load.items()):
            cap = cap_by_slot.get(slot, 10**9)
            if count <= cap:
                continue

            # candidatos no slot
            uids_here = [u for u, s in assignment.items() if s == slot]

            # filtrar por quota (se fornecido)
            if movable_users is not None:
                uids_here = [u for u in uids_here if u in movable_users]

            # ordenar por prioridade (fairness: quem tem menor fairness_score primeiro, etc.)
            if priority_order:
                order_index = {u: i for i, u in enumerate(priority_order)}
                uids_here.sort(key=lambda u: order_index.get(u, 10**9))

            for uid in uids_here:
                alts = user_alternatives.get(uid, [])
                if slot in alts:
                    idx = alts.index(slot)
                    for nxt in alts[idx+1:]:
                        if load[nxt] < cap_by_slot.get(nxt, 10**9):
                            assignment[uid] = nxt
                            load[slot] -= 1
                            load[nxt] += 1
                            changed = True
                            break
                if load[slot] <= cap:
                    break

    return assignment
