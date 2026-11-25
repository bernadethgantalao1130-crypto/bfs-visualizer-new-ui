"""BFS logic (no GUI). Records one snapshot per executed line.

Counters:
  Passes      = nodes fully expanded (one trip around the while loop)
  Comparisons = visited-set checks
  Shifts      = queue.shift() / popleft calls

Family-tree support:
  * load_family_csv()  reads a relations CSV (person_a, person_b, relation)
  * load_scenarios()   reads data/scenarios.csv (best / average / worst cases)
  * evaluate()         runs one scenario and reports how much work BFS did
"""
import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"

# ---------- card size and spacing (shared with main.py) ----------
CARD_W, CARD_H = 100, 104      # one person card
GAP_X = 112                    # distance between two cards in a row
ROW_GAP = 150                  # distance between two generations
MARGIN = 30                    # empty space around the whole tree

# ---------- built-in demo graph (the original A-I graph) ----------
POS = {"A": (310, 80), "B": (150, 230), "C": (470, 230), "D": (70, 380),
       "E": (240, 380), "F": (390, 380), "G": (550, 380), "H": (150, 530),
       "I": (470, 530)}
EDGES = [("A", "B"), ("A", "C"), ("B", "D"), ("B", "E"), ("C", "F"), ("C", "G"),
         ("E", "H"), ("F", "I"), ("E", "F"), ("D", "H"), ("G", "I")]


def make_adj(nodes, edges):
    adj = {k: [] for k in nodes}
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    return adj


ADJ = make_adj(POS, EDGES)

CODE = [
    "def bfs(graph, start, target, order):",
    "    visited = {start}",
    "    queue = [start]",
    "    while queue:",
    "        node = queue.pop(0)          # shift",
    "        for nb in sorted(graph[node], reverse=order):",
    "            if nb not in visited:    # comparison",
    "                visited.add(nb)",
    "                if nb == target:     # goal test",
    "                    return \"found\"",
    "                queue.append(nb)",
    "",
    "        # pass complete",
    "    return \"not found\"",
]
L_DEF, L_VISIT, L_QUEUE, L_WHILE, L_SHIFT, L_FOR, L_CMP, L_MARK, L_GOAL, \
    L_FOUND, L_PUSH, _, L_PASS, L_END = range(14)


# ---------- family tree graphs ----------
class Graph:
    """A graph plus everything the GUI needs to draw it."""

    def __init__(self, name, people, edges, kinds, pos, size):
        self.name, self.people, self.edges = name, people, edges
        self.kinds, self.pos, self.size = kinds, pos, size
        self.adj = make_adj(people, edges)


def demo_graph():
    return Graph("A-I graph", list(POS), EDGES, {}, POS, (620, 600))


def load_family_csv(path):
    """Read a relations CSV.

    Columns: person_a, person_b, relation
      relation = parent   -> person_a is a parent of person_b
      relation = spouse   -> person_a and person_b are partners
      relation = sibling  -> person_a and person_b are siblings
    Lines starting with # are ignored.
    """
    path = Path(path)
    people, edges, kinds = [], [], {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        rd = csv.DictReader(f)
        need = {"person_a", "person_b", "relation"}
        if not rd.fieldnames or not need <= set(rd.fieldnames):
            raise ValueError(f"{path.name}: header must be person_a,person_b,relation")
        for n, row in enumerate(rd, start=2):
            a = (row["person_a"] or "").strip()
            b = (row["person_b"] or "").strip()
            rel = (row["relation"] or "").strip().lower()
            if not a or a.startswith("#"):
                continue
            if not b:                      # a lone person with no links (leave b and relation empty)
                if a not in people:
                    people.append(a)
                continue
            if rel not in ("parent", "spouse", "sibling"):
                raise ValueError(f"{path.name} line {n}: relation must be "
                                 f"parent, spouse or sibling (got '{rel}')")
            for p in (a, b):
                if p not in people:
                    people.append(p)
            if (a, b) not in edges and (b, a) not in edges:
                edges.append((a, b))
                kinds[(a, b)] = rel
    pos, size = layout(people, edges, kinds)
    return Graph(path.stem, people, edges, kinds, pos, size)


def layout(people, edges, kinds):
    """Generation rows: parents above children, spouses side by side.

    Returns (positions, (width, height)). Every card gets the same spacing, so
    big families make a big picture (the GUI scrolls) instead of overlapping cards.
    """
    spouses = {p: [] for p in people}
    kids = {p: [] for p in people}
    parents = {p: [] for p in people}
    nbrs = make_adj(people, edges)
    for a, b in edges:
        k = kinds.get((a, b), "spouse")
        if k == "parent":
            kids[a].append(b)
            parents[b].append(a)
        else:
            spouses[a].append(b)
            spouses[b].append(a)

    # 1) generation number, one connected family at a time
    gen, comp = {}, {}
    comps = []
    for p in people:
        if p in gen:
            continue
        gen[p], comp[p] = 0, len(comps)
        members, todo = [p], [p]
        while todo:
            x = todo.pop(0)
            for y in nbrs[x]:
                if y in gen:
                    continue
                k = kinds.get((x, y)) or kinds.get((y, x))
                if k == "parent":
                    gen[y] = gen[x] + (1 if y in kids[x] else -1)
                else:
                    gen[y] = gen[x]
                comp[y] = comp[p]
                members.append(y)
                todo.append(y)
        low = min(gen[m] for m in members)
        for m in members:
            gen[m] -= low
        comps.append(members)

    # 2) left-to-right order inside each row (spouse next to spouse)
    seen, order = set(), []

    def place(p):
        if p in seen:
            return
        seen.add(p)
        order.append(p)
        for s in spouses[p]:
            if s not in seen:
                seen.add(s)
                order.append(s)
        for c in kids[p] + [c for s in spouses[p] for c in kids[s]]:
            place(c)

    for members in comps:
        tops = [m for m in members if not parents[m]]
        tops.sort(key=lambda m: (gen[m], people.index(m)))
        for m in tops:
            place(m)
        for m in members:
            place(m)

    rows = {}
    for p in order:
        rows.setdefault(gen[p], []).append(p)
    deepest = max(rows) if rows else 0
    widest = max(len(r) for r in rows.values()) if rows else 1
    W = widest * GAP_X + 2 * MARGIN
    H = deepest * ROW_GAP + CARD_H + 2 * MARGIN
    pos = {}
    for g, row in rows.items():
        y = MARGIN + CARD_H / 2 + g * ROW_GAP
        x0 = W / 2 - GAP_X * (len(row) - 1) / 2          # center each row
        for i, p in enumerate(row):
            pos[p] = (round(x0 + i * GAP_X), round(y))
    return pos, (W, H)


# ---------- the BFS step recorder ----------
def build_steps(start, descending, target=None, adj=None):
    """Run BFS once and record a snapshot for every line that executes."""
    adj = ADJ if adj is None else adj
    visited, queue, done, order, tree, dist = set(), [], [], [], [], {}
    c = {"pass": 0, "cmp": 0, "shift": 0}
    steps = []
    found = [None]

    def snap(line, cur, act, note):
        steps.append(dict(line=line, cur=cur, act=act, note=note, found=found[0],
                          target=target, q=list(queue), done=list(done),
                          order=list(order), tree=list(tree), dist=dict(dist), **c))

    goal = f" Looking for {target}." if target else " No target: full traversal."
    snap(L_DEF, None, None, f"Start BFS from {start}, neighbors in "
                            f"{'descending' if descending else 'ascending'} order." + goal)
    visited.add(start)
    dist[start] = 0
    snap(L_VISIT, None, None, f"Mark {start} visited so it is never queued twice.")
    queue.append(start)
    snap(L_QUEUE, None, None, f"Put {start} in the queue.")
    if target == start:
        found[0] = start
        snap(L_FOUND, start, None, f"{start} is the target already: found with "
                                   f"0 passes, 0 comparisons, 0 shifts.")
        return steps
    while queue:
        snap(L_WHILE, None, None, f"Queue has {len(queue)} item(s), loop continues.")
        node = queue.pop(0)
        c["shift"] += 1
        order.append(node)
        snap(L_SHIFT, node, None, f"Shift {node} off the front. Shifts: {c['shift']}.")
        for nb in sorted(adj[node], reverse=descending):
            snap(L_FOR, node, (node, nb), f"Look at neighbor {nb} of {node}.")
            c["cmp"] += 1
            if nb not in visited:
                snap(L_CMP, node, (node, nb),
                     f"Comparison {c['cmp']}: {nb} not visited yet.")
                visited.add(nb)
                dist[nb] = dist[node] + 1
                tree.append((node, nb))
                snap(L_MARK, node, (node, nb),
                     f"Mark {nb} visited (distance {dist[nb]}).")
                if target is not None:
                    snap(L_GOAL, node, (node, nb),
                         f"Goal test: is {nb} the target {target}? "
                         f"{'Yes!' if nb == target else 'No.'}")
                    if nb == target:
                        found[0] = nb
                        snap(L_FOUND, node, (node, nb),
                             f"Found {target}, {dist[nb]} link(s) from {start}. "
                             f"Work: {c['shift']} shifts + {c['cmp']} comparisons.")
                        return steps
                queue.append(nb)
                snap(L_PUSH, node, (node, nb), f"Push {nb} to the back of the queue.")
            else:
                snap(L_CMP, node, (node, nb),
                     f"Comparison {c['cmp']}: {nb} already visited, skip.")
        done.append(node)
        c["pass"] += 1
        snap(L_PASS, node, None, f"Pass {c['pass']} complete: {node} fully expanded.")
    if target is None:
        snap(L_END, None, None, f"Queue empty. Visit order: {', '.join(order)}.")
    else:
        snap(L_END, None, None, f"Queue empty. {target} was never reached: it is not "
                                f"connected to {start}. Whole family explored.")
    return steps


# ---------- best / average / worst case scenarios ----------
def classify(pct):
    """Label how much of a full traversal the search needed."""
    return "BEST" if pct <= 20 else "WORST" if pct >= 80 else "AVERAGE"


def evaluate(graph, start, target, descending=False):
    """Run BFS and compare its work with a complete traversal from `start`."""
    last = build_steps(start, descending, target, graph.adj)[-1]
    full = build_steps(start, descending, None, graph.adj)[-1]
    work = last["shift"] + last["cmp"]
    full_work = full["shift"] + full["cmp"]
    pct = round(100 * work / full_work, 1) if full_work else 0.0
    return dict(people=len(graph.people), links=len(graph.edges),
                found=bool(last["found"]), distance=last["dist"].get(target),
                passes=last["pass"], comparisons=last["cmp"], shifts=last["shift"],
                work=work, full_work=full_work, pct=pct, measured=classify(pct))


def load_scenarios(data_dir=DATA_DIR):
    """Read data/scenarios.csv: file, case, title, example, start, target, why."""
    out = []
    with open(Path(data_dir) / "scenarios.csv", newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            row = {k: (v or "").strip() for k, v in row.items()}
            row["path"] = Path(data_dir) / row["file"]
            out.append(row)
    return out


def evaluate_all(descending=False, data_dir=DATA_DIR):
    """One result row per scenario, ready to print or save as CSV."""
    rows = []
    for sc in load_scenarios(data_dir):
        g = load_family_csv(sc["path"])
        r = evaluate(g, sc["start"], sc["target"] or None, descending)
        rows.append(dict(case=sc["case"], file=sc["file"], title=sc["title"],
                         start=sc["start"], target=sc["target"],
                         order="descending" if descending else "ascending", **r))
    return rows
