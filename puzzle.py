# puzzle.py — 8-puzzle core logic + A* (Manhattan) + helpers
from dataclasses import dataclass, field
from typing import Tuple, List, Dict, Optional
import heapq, random

State = Tuple[int, ...]            # 9 ints 0..8; 0 = blank
GOAL: State = (1,2,3,4,5,6,7,8,0)

def index_to_rc(i: int) -> Tuple[int,int]:
    return divmod(i, 3)

def rc_to_index(r: int, c: int) -> int:
    return r*3 + c

def is_solved(s: State) -> bool:
    return s == GOAL

def is_solvable(state: State) -> bool:
    arr = [x for x in state if x != 0]
    inv = 0
    for i in range(len(arr)):
        for j in range(i+1, len(arr)):
            inv += arr[i] > arr[j]
    return inv % 2 == 0

def neighbors(state: State) -> List[State]:
    out: List[State] = []
    z = state.index(0)
    zr, zc = index_to_rc(z)
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        r, c = zr+dr, zc+dc
        if 0 <= r < 3 and 0 <= c < 3:
            j = rc_to_index(r, c)
            s = list(state)
            s[z], s[j] = s[j], s[z]
            out.append(tuple(s))
    return out

def manhattan(state: State) -> int:
    total = 0
    for i, v in enumerate(state):
        if v == 0: 
            continue
        r, c = index_to_rc(i)
        gr, gc = index_to_rc(v-1)
        total += abs(r-gr) + abs(c-gc)
    return total

@dataclass(order=True)
class Node:
    f: int
    state: State = field(compare=False)
    g: int = field(compare=False)
    parent: Optional["Node"] = field(compare=False, default=None)

def _reconstruct(n: Node) -> List[State]:
    path: List[State] = []
    while n is not None:
        path.append(n.state)
        n = n.parent
    path.reverse()
    return path

def a_star(start: State):
    if is_solved(start):
        return [start], {"expanded": 0, "length": 0}
    openh: List[Node] = []
    gbest: Dict[State, int] = {start: 0}
    heapq.heappush(openh, Node(manhattan(start), start, 0, None))
    best_seen_g: Dict[State, int] = {}
    expanded = 0
    while openh:
        cur = heapq.heappop(openh)
        if cur.state in best_seen_g and best_seen_g[cur.state] < cur.g:
            continue
        if is_solved(cur.state):
            path = _reconstruct(cur)
            return path, {"expanded": expanded, "length": len(path)-1}
        best_seen_g[cur.state] = cur.g
        expanded += 1
        for nxt in neighbors(cur.state):
            g2 = cur.g + 1
            if nxt not in gbest or g2 < gbest[nxt]:
                gbest[nxt] = g2
                heapq.heappush(openh, Node(g2 + manhattan(nxt), nxt, g2, cur))
    return [], {"expanded": expanded, "length": 0}

def can_slide(state: State, tile_index: int) -> bool:
    z = state.index(0)
    zr, zc = index_to_rc(z)
    r, c = index_to_rc(tile_index)
    return abs(zr - r) + abs(zc - c) == 1

def slide_if_adjacent(state: State, tile_index: int) -> State:
    if not can_slide(state, tile_index):
        return state
    s = list(state)
    z = s.index(0)
    s[z], s[tile_index] = s[tile_index], s[z]
    return tuple(s)

def scramble_via_random_walk(steps: int = 50, seed: Optional[int] = None) -> State:
    rng = random.Random(seed)
    s = list(GOAL)
    z = s.index(0)
    zr, zc = index_to_rc(z)
    last_swap = None
    for _ in range(steps):
        opts = []
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            r, c = zr+dr, zc+dc
            if 0 <= r < 3 and 0 <= c < 3:
                j = rc_to_index(r, c)
                opts.append(j)
        if last_swap in opts and len(opts) > 1:
            opts.remove(last_swap)
        j = rng.choice(opts)
        s[z], s[j] = s[j], s[z]
        last_swap = z
        z = j
        zr, zc = index_to_rc(z)
    return tuple(s)
