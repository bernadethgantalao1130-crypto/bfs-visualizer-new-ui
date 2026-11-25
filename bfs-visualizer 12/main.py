"""BFS visualizer GUI - pure Python (tkinter, standard library only).

Run:  python main.py
Left-click a card = start node.  Right-click a card = target node.
Pick one of the family-tree scenarios (best / average / worst case) from the
Scenario box, or load your own relations CSV.

The look follows a green "family tree" dashboard: green sidebar, white top bar,
person cards with round avatars and square (elbow) connector lines.
"""
import csv
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, font as tkfont, messagebox, ttk

from bfs_core import (CARD_H, CARD_W, CODE, build_steps, classify, demo_graph,
                      evaluate_all, load_family_csv, load_scenarios)

# ---------- colors ----------
BG = "#eef7f3"                      # page background (light mint)
PANEL, BORDER = "#ffffff", "#dde6e1"
INK, MUTE = "#1d2b26", "#7b8a84"
SIDEBAR, SIDEBAR_DARK, SIDEBAR_ON = "#33c36b", "#2aa95b", "#4ad483"
GREEN, GREEN_DARK, GREEN_SOFT = "#2ecc71", "#1fa85a", "#eaf8f0"
PURPLE, BLUE, BLACK = "#9b8cf5", "#1fb0f0", "#111111"
ORANGE, RED, GOLD = "#ff9f1a", "#f0545b", "#f4b740"
LINE = "#2b3a34"                    # connector lines (dark, like the design)
CASE_COLOR = {"BEST": GREEN, "AVERAGE": GOLD, "WORST": "#ed6a5a"}

DEMO, NONE = "A-I graph", "(none)"  # DEMO is only a fallback if data/ is missing
HINT = "Search for family members..."
METER_W = 420

FONT = "Segoe UI"                   # App.__init__ switches to Poppins if it is installed


def f(size, bold=False):
    """Small helper so every font is written the same way."""
    return (FONT, size, "bold") if bold else (FONT, size)


# ---------- avatars ----------
SKINS = ["#f6d2b0", "#e2b28d", "#c68a5d", "#8d5a3b"]
HAIRS = ["#2b1b17", "#4b2f28", "#d5a44a", "#a0522d", "#9aa0a6"]
SHIRTS = ["#6c8cd5", "#e57373", "#5fbf8f", "#f2a65a", "#9b8cf5", "#4a5568"]


def draw_avatar(cv, x, y, r, name):
    """Round cartoon face. The same name always gets the same face."""
    n = sum(ord(c) * (i + 1) for i, c in enumerate(name))
    skin, hair, shirt = SKINS[n % 4], HAIRS[n // 4 % 5], SHIRTS[n // 20 % 6]
    long_hair, glasses = n // 120 % 2 == 0, n // 240 % 3 == 0

    cv.create_oval(x - r, y - r, x + r, y + r, fill="#fcebdc", outline="")   # background
    base = y + 0.78 * r                                                      # shoulders
    cv.create_arc(x - 0.62 * r, base - 0.55 * r, x + 0.62 * r, base + 0.55 * r,
                  start=0, extent=180, fill=shirt, outline="", style="pieslice")
    hy = y - 0.12 * r                                                        # head center
    if long_hair:                                                            # hair falling past the face
        for side in (-1, 1):
            cv.create_oval(x + side * 0.30 * r - 0.14 * r, hy - 0.25 * r,
                           x + side * 0.30 * r + 0.14 * r, hy + 0.62 * r,
                           fill=hair, outline="")
    cv.create_oval(x - 0.34 * r, hy - 0.38 * r, x + 0.34 * r, hy + 0.38 * r,
                   fill=skin, outline="")
    cv.create_arc(x - 0.37 * r, hy - 0.42 * r, x + 0.37 * r, hy + 0.34 * r,
                  start=10, extent=160, fill=hair, outline=hair, style="pieslice")
    for side in (-1, 1):                                                     # eyes
        ex = x + side * 0.13 * r
        cv.create_oval(ex - 1.5, hy, ex + 1.5, hy + 3, fill=INK, outline="")
        if glasses:
            cv.create_oval(ex - 0.11 * r, hy - 0.06 * r, ex + 0.11 * r, hy + 0.16 * r,
                           outline=INK)
    cv.create_arc(x - 0.14 * r, hy + 0.06 * r, x + 0.14 * r, hy + 0.24 * r,
                  start=200, extent=140, style="arc", outline=INK)           # smile


# ---------- rounded button / label ----------
class Pill(tk.Canvas):
    """A rounded button drawn on a canvas (normal tk buttons cannot have round corners).

    command=None makes it a plain label. icon=True adds the green smiley circle.
    """

    def __init__(self, parent, text, command=None, bg=GREEN, fg="white",
                 behind=PANEL, size=10, icon=False, padx=16, pady=7):
        self.fill, self.fg, self.icon, self.padx, self.pady = bg, fg, icon, padx, pady
        self.font = tkfont.Font(family=FONT, size=size, weight="bold")
        super().__init__(parent, bg=behind, highlightthickness=0, bd=0)
        if command:
            self.config(cursor="hand2")
            self.bind("<Button-1>", lambda e: command())
            self.bind("<Enter>", lambda e: self.itemconfig("shape", fill=self.darker()))
            self.bind("<Leave>", lambda e: self.itemconfig("shape", fill=self.fill))
        self.set_text(text)

    def darker(self):
        """Slightly darker version of the button color (for hover)."""
        r, g, b = (int(self.fill[i:i + 2], 16) for i in (1, 3, 5))
        return "#%02x%02x%02x" % (int(r * 0.88), int(g * 0.88), int(b * 0.88))

    def set_text(self, text):
        self.delete("all")
        left = self.padx + (30 if self.icon else 0)
        w = self.font.measure(text) + left + self.padx
        h = self.font.metrics("linespace") + 2 * self.pady
        self.config(width=w, height=h)
        self.create_oval(0, 0, h, h, fill=self.fill, outline="", tags="shape")
        self.create_oval(w - h, 0, w, h, fill=self.fill, outline="", tags="shape")
        self.create_rectangle(h / 2, 0, w - h / 2, h, fill=self.fill, outline="", tags="shape")
        if self.icon:
            self.create_oval(8, h / 2 - 12, 32, h / 2 + 12, fill=GREEN, outline="")
            self.create_text(20, h / 2, text="\u263a", fill="white", font=f(12, True))
        self.create_text(left, h / 2, text=text, anchor="w", fill=self.fg, font=self.font)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        global FONT
        if "Poppins" in tkfont.families():
            FONT = "Poppins"
        self.title("Family Tree - Real-Life BFS")
        self.configure(bg=BG)
        self.geometry("1240x820")
        self.minsize(1100, 700)
        self.steps, self.idx, self.job = [], 0, None
        self.g, self.sc = demo_graph(), None
        self.full_work, self.final_work = 1, 0
        self.ox, self.oy = 0, 0               # offset that centers a small tree
        self.canvas_size = (0, 0)
        self.cache = {}                       # scenario name -> Graph
        self.scenarios = []
        try:
            self.scenarios = load_scenarios()
        except OSError:
            pass                              # data/ folder missing: demo graph only
        self.names = [f"{s['case']}: {s['title']}" for s in self.scenarios] or [DEMO]
        self._ui()
        self.on_scenario()

    # ---------- layout ----------
    def _ui(self):
        st = ttk.Style(self)
        st.theme_use("clam")
        st.configure("TCombobox", fieldbackground="white", background="white",
                     foreground=INK, arrowcolor=INK, bordercolor=BORDER)
        st.configure("TButton", background=GREEN_DARK, foreground="white",
                     padding=(14, 7), relief="flat", borderwidth=0, font=f(9, True))
        st.map("TButton", background=[("active", GREEN)])
        st.configure("Treeview", background="white", fieldbackground="white",
                     foreground=INK, rowheight=26, borderwidth=0)
        st.configure("Treeview.Heading", background=GREEN_DARK, foreground="white",
                     relief="flat")
        st.map("Treeview", background=[("selected", GREEN_DARK)])
        st.configure("TScrollbar", background=BORDER, troughcolor=PANEL,
                     bordercolor=PANEL, arrowcolor=MUTE)
        self.option_add("*TCombobox*Listbox.background", "white")
        self.option_add("*TCombobox*Listbox.foreground", INK)

        root = tk.Frame(self, bg=BG)
        root.pack(fill="both", expand=True)

        self._sidebar(root)
        main = tk.Frame(root, bg=BG)
        main.pack(side="left", fill="both", expand=True)
        self._header(main)
        self._toolbar(main)

        body = tk.Frame(main, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=(8, 12))
        self._tree_column(body)
        self._right_panel(body)

    def _sidebar(self, root):
        sidebar = tk.Frame(root, bg=SIDEBAR, width=64)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # logo: a little pine tree made of three triangles and a trunk
        logo = tk.Canvas(sidebar, width=64, height=64, bg=SIDEBAR_DARK, highlightthickness=0)
        logo.pack()
        for top, half in ((12, 10), (21, 14), (30, 18)):
            logo.create_polygon(32, top, 32 - half, top + 14, 32 + half, top + 14,
                                fill="white", outline="")
        logo.create_rectangle(29, 44, 35, 52, fill="white", outline="")

        for i, icon in enumerate(("⌂", "⚙", "◎", "♧", "?", "✉", "▣", "⏻")):
            bg = SIDEBAR_ON if i == 0 else SIDEBAR        # the first icon is the page we are on
            tk.Button(sidebar, text=icon, bg=bg, fg="white", activebackground=SIDEBAR_ON,
                      activeforeground="white", relief="flat", bd=0, font=f(14),
                      height=2).pack(fill="x")
            tk.Frame(sidebar, bg=SIDEBAR_DARK, height=1).pack(fill="x")

    def _header(self, main):
        header = tk.Frame(main, bg=PANEL, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        # search box with a green button on the right
        box = tk.Frame(header, bg=BORDER, padx=1, pady=1)
        box.pack(side="left", padx=24)
        inner = tk.Frame(box, bg="white")
        inner.pack()
        self.search = tk.Entry(inner, width=46, bg="white", fg=MUTE, relief="flat", bd=0,
                               font=f(10), insertbackground=INK)
        self.search.pack(side="left", padx=(12, 6), ipady=7)
        self.search.insert(0, HINT)
        self.search.bind("<FocusIn>", self.clear_hint)
        self.search.bind("<Return>", lambda e: self.search_scenarios())
        tk.Button(inner, text="\u26b2", command=self.search_scenarios, bg=GREEN_DARK,
                  fg="white", activebackground=GREEN, activeforeground="white",
                  relief="flat", bd=0, font=f(11), width=3).pack(side="left", padx=4, pady=4)

        # right side, packed from right to left: user, divider, create button, bell, gear
        user = tk.Frame(header, bg=PANEL)
        user.pack(side="right", padx=(10, 24))
        face = tk.Canvas(user, width=38, height=38, bg=PANEL, highlightthickness=0)
        face.pack(side="left")
        face.create_oval(1, 1, 37, 37, fill="#d9dcdb", outline="")
        face.create_oval(13, 7, 25, 19, fill="#a4abaa", outline="")
        face.create_arc(7, 21, 31, 47, start=0, extent=180, fill="#a4abaa", outline="")
        tk.Label(user, text="khalid", bg=PANEL, fg=INK, font=f(10, True)).pack(side="left", padx=8)
        tk.Frame(header, bg=BORDER, width=1, height=34).pack(side="right", padx=8)
        Pill(header, "+  Create a tree", self.load_csv, bg=PURPLE, behind=PANEL,
             size=9).pack(side="right", padx=8)

        bell = tk.Canvas(header, width=34, height=38, bg=PANEL, highlightthickness=0)
        bell.pack(side="right", padx=8)
        bell.create_oval(9, 8, 25, 24, fill=GREEN_DARK, outline="")        # dome
        bell.create_rectangle(9, 16, 25, 26, fill=GREEN_DARK, outline="")
        bell.create_rectangle(6, 25, 28, 28, fill=GREEN_DARK, outline="")  # rim
        bell.create_oval(14, 27, 20, 33, fill=GREEN_DARK, outline="")      # clapper
        bell.create_oval(19, 3, 31, 15, fill=RED, outline="")              # red badge
        bell.create_text(25, 9, text="2", fill="white", font=f(7, True))

        gear = tk.Canvas(header, width=36, height=36, bg=PANEL, highlightthickness=0)
        gear.pack(side="right", padx=8)
        gear.create_oval(1, 1, 35, 35, fill=ORANGE, outline="")
        gear.create_text(18, 18, text="⚙", fill="white", font=f(13))

    def _toolbar(self, main):
        toolbar = tk.Frame(main, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        toolbar.pack(fill="x", padx=16, pady=(12, 0))
        self.scn = tk.StringVar(value=self.names[0])
        self.start = tk.StringVar(value="A")
        self.target = tk.StringVar(value=NONE)
        self.order = tk.StringVar(value="Ascending")
        self.cbs = {}
        for key, text, var, vals, width, cmd in (
                ("scn", "Scenario", self.scn, self.names, 50, self.on_scenario),
                ("start", "Start", self.start, [], 8, self.build),
                ("target", "Target", self.target, [NONE], 8, self.build),
                ("order", "Order", self.order, ["Ascending", "Descending"], 11,
                 self.build)):
            tk.Label(toolbar, text=text, bg=PANEL, fg=MUTE,
                     font=f(9)).pack(side="left", padx=(10, 3))
            cb = ttk.Combobox(toolbar, textvariable=var, values=vals, width=width,
                              state="readonly")
            cb.pack(side="left", pady=7)
            cb.bind("<<ComboboxSelected>>", lambda e, fn=cmd: fn())
            self.cbs[key] = cb

    def _tree_column(self, body):
        col = tk.Frame(body, bg=BG)
        col.pack(side="left", fill="both", expand=True)

        # title pill on the left, action buttons on the right
        title_row = tk.Frame(col, bg=BG)
        title_row.pack(fill="x", pady=(2, 8))
        self.tree_title = Pill(title_row, "Puerto's Family Tree:", bg="#e3e6e4", fg=INK,
                               behind=BG, size=12, icon=True)
        self.tree_title.pack(side="left")
        for text, cmd, color in (("Compare", self.compare, GREEN),
                                 ("Edit", self.load_csv, BLUE),
                                 ("Share", lambda: None, BLACK)):
            Pill(title_row, text, cmd, bg=color, behind=BG, size=9,
                 padx=14, pady=5).pack(side="right", padx=3)

        # the tree itself: canvas with scrollbars for big families
        wrap = tk.Frame(col, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        wrap.pack(fill="both", expand=True)
        wrap.rowconfigure(0, weight=1)
        wrap.columnconfigure(0, weight=1)
        self.cv = tk.Canvas(wrap, width=700, height=380, bg=PANEL, highlightthickness=0)
        self.cv.grid(row=0, column=0, sticky="nsew")
        vbar = ttk.Scrollbar(wrap, orient="vertical", command=self.cv.yview)
        hbar = ttk.Scrollbar(wrap, orient="horizontal", command=self.cv.xview)
        vbar.grid(row=0, column=1, sticky="ns")
        hbar.grid(row=1, column=0, sticky="ew")
        self.cv.config(yscrollcommand=vbar.set, xscrollcommand=hbar.set)
        self.cv.bind("<Button-1>", self.pick_start)
        self.cv.bind("<Button-2>", self.pick_target)
        self.cv.bind("<Button-3>", self.pick_target)
        self.cv.bind("<MouseWheel>", self.on_wheel)       # Windows / macOS
        self.cv.bind("<Button-4>", self.on_wheel)         # Linux
        self.cv.bind("<Button-5>", self.on_wheel)
        self.cv.bind("<Configure>", self.on_resize)

        # case card under the tree
        strip = tk.Frame(col, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        strip.pack(fill="x", pady=(8, 0))
        head = tk.Frame(strip, bg=PANEL)
        head.pack(fill="x", padx=14, pady=(10, 0))
        self.badge = tk.Label(head, text="", bg=GREEN_DARK, fg="white", padx=10, pady=2,
                              font=f(9, True))
        self.badge.pack(side="left")
        self.ttl = tk.Label(head, bg=PANEL, fg=INK, font=f(11, True), anchor="w")
        self.ttl.pack(side="left", padx=10)
        self.ex = tk.Label(strip, bg=PANEL, fg=INK, font=f(9), anchor="w",
                           justify="left", wraplength=700)
        self.ex.pack(fill="x", padx=14, pady=(6, 0))
        self.why = tk.Label(strip, bg=PANEL, fg=MUTE, font=f(9), anchor="w",
                            justify="left", wraplength=700)
        self.why.pack(fill="x", padx=14, pady=(4, 0))
        self.meter_lbl = tk.Label(strip, bg=PANEL, fg=INK, font=f(9, True), anchor="w",
                                  justify="left", wraplength=700)
        self.meter_lbl.pack(fill="x", padx=14, pady=(8, 3))
        self.meter = tk.Canvas(strip, width=METER_W, height=12, bg=PANEL,
                               highlightthickness=0)
        self.meter.pack(anchor="w", padx=14, pady=(0, 10))
        strip.bind("<Configure>", self.wrap_strip)

        tk.Label(col, text="Left-click a card = start    |    Right-click a card = target"
                           "    |    Mouse wheel scrolls big families",
                 bg=BG, fg=MUTE, font=f(8)).pack(pady=(6, 0))

    def _right_panel(self, body):
        right = tk.Frame(body, bg=PANEL, width=290, highlightbackground=BORDER,
                         highlightthickness=1)
        right.pack(side="left", fill="y", padx=(12, 0))
        right.pack_propagate(False)

        control = tk.Frame(right, bg=PANEL)
        control.pack(fill="x", padx=14, pady=(14, 6))
        tk.Label(control, text="BFS Controls", bg=PANEL, fg=INK,
                 font=f(12, True)).pack(anchor="w")
        buttons = tk.Frame(control, bg=PANEL)
        buttons.pack(anchor="w", pady=8)
        self.play_btn = ttk.Button(buttons, text="Play", command=self.toggle, width=7)
        self.play_btn.pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="Step", command=lambda: self.go(1),
                   width=7).pack(side="left", padx=6)
        ttk.Button(buttons, text="Reset", command=self.reset,
                   width=7).pack(side="left", padx=6)
        tk.Label(control, text="Speed", bg=PANEL, fg=MUTE, font=f(8)).pack(anchor="w")
        self.speed = tk.Scale(control, from_=1, to=10, orient="horizontal", length=220,
                              bg=PANEL, fg=INK, troughcolor=GREEN_SOFT,
                              highlightthickness=0, bd=0)
        self.speed.set(5)
        self.speed.pack(anchor="w")

        stats = tk.Frame(right, bg=PANEL)
        stats.pack(fill="x", padx=11)
        self.sv = {}
        for key, label in (("pass", "Passes"), ("cmp", "Comparisons"), ("shift", "Shifts")):
            box = tk.Frame(stats, bg=GREEN_SOFT)
            box.pack(side="left", expand=True, fill="x", padx=3)
            self.sv[key] = tk.Label(box, text="0", bg=GREEN_SOFT, fg=GREEN_DARK,
                                    font=f(16, True))
            self.sv[key].pack(pady=(5, 0))
            tk.Label(box, text=label, bg=GREEN_SOFT, fg=MUTE, font=f(8)).pack(pady=(0, 5))

        self.code = tk.Text(right, width=36, height=len(CODE), bg="#f6faf8", fg=MUTE,
                            font=("Consolas", 9), relief="flat", cursor="arrow")
        self.code.pack(padx=14, pady=10, fill="x")
        self.code.insert("1.0", "\n".join(CODE))
        self.code.tag_config("on", background="#d6f3e2", foreground=INK)
        self.code.config(state="disabled")

        info = tk.Frame(right, bg=PANEL)
        info.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        self.q_lbl = tk.Label(info, bg=PANEL, fg=INK, font=f(9), anchor="w",
                              wraplength=250, justify="left")
        self.o_lbl = tk.Label(info, bg=PANEL, fg=INK, font=f(9), anchor="w",
                              wraplength=250, justify="left")
        self.note = tk.Label(info, bg=GREEN_SOFT, fg=INK, font=f(9), anchor="w",
                             padx=8, pady=6, wraplength=250, justify="left")
        for w in (self.q_lbl, self.o_lbl, self.note):
            w.pack(fill="x", pady=3)

    # ---------- small window helpers ----------
    def clear_hint(self, e):
        if self.search.get() == HINT:
            self.search.delete(0, "end")
        self.search.config(fg=INK)

    def wrap_strip(self, e):
        """Keep the long texts of the case card as wide as the card."""
        width = max(300, e.width - 30)
        for label in (self.ex, self.why, self.meter_lbl):
            label.config(wraplength=width)

    def on_resize(self, e):
        if self.steps and (e.width, e.height) != self.canvas_size:
            self.canvas_size = (e.width, e.height)
            self.render()                       # re-center the tree

    def on_wheel(self, e):
        step = -1 if (e.num == 4 or e.delta > 0) else 1
        if e.state & 1:                         # Shift held: scroll sideways
            self.cv.xview_scroll(step, "units")
        else:
            self.cv.yview_scroll(step, "units")

    # ---------- choosing a graph ----------
    def on_scenario(self):
        name = self.scn.get()
        self.sc = next((s for s in self.scenarios
                        if f"{s['case']}: {s['title']}" == name), None)
        self.tree_title.set_text(self.sc["title"] if self.sc else "Puerto's Family Tree:")
        if name == DEMO:
            self.g = demo_graph()
            start, target = "A", NONE
        elif self.sc:
            try:
                if name not in self.cache:
                    self.cache[name] = load_family_csv(self.sc["path"])
            except (OSError, ValueError) as err:
                messagebox.showerror("Cannot load scenario", str(err))
                self.scn.set(DEMO)
                return self.on_scenario()
            self.g = self.cache[name]
            start, target = self.sc["start"], self.sc["target"] or NONE
        else:                                   # a CSV the user loaded
            self.g = self.cache[name]
            start, target = self.g.people[0], NONE
        self.cbs["start"].config(values=self.g.people)
        self.cbs["target"].config(values=[NONE] + self.g.people)
        self.start.set(start)
        self.target.set(target)
        self.cv.xview_moveto(0)
        self.cv.yview_moveto(0)
        self.build()

    def load_csv(self):
        path = filedialog.askopenfilename(
            title="Open a family relations CSV (person_a, person_b, relation)",
            initialdir=Path(__file__).resolve().parent / "data",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not path:
            return
        try:
            g = load_family_csv(path)
            if not g.people:
                raise ValueError("The file has no people in it.")
        except (OSError, ValueError) as err:
            messagebox.showerror("Cannot load CSV", str(err))
            return
        name = f"Custom: {Path(path).name}"
        self.cache[name] = g
        if name not in self.names:
            self.names.append(name)
            self.cbs["scn"].config(values=self.names)
        self.scn.set(name)
        self.on_scenario()

    def search_scenarios(self):
        query = self.search.get().strip().lower()
        if not query or query == HINT.lower():
            return
        for name in self.names:
            if query in name.lower():
                self.scn.set(name)
                self.on_scenario()
                return
        for person in self.g.people:
            if query in person.lower():
                self.target.set(person)
                self.build()
                return

    def kind(self, a, b):
        return self.g.kinds.get((a, b)) or self.g.kinds.get((b, a))

    def at(self, k):
        """Where card k is on the canvas (tree position + centering offset)."""
        x, y = self.g.pos[k]
        return x + self.ox, y + self.oy

    def hit(self, e):
        """Which card is under the mouse? (works while the canvas is scrolled)"""
        mx, my = self.cv.canvasx(e.x), self.cv.canvasy(e.y)
        for k in self.g.pos:
            x, y = self.at(k)
            if abs(mx - x) <= CARD_W / 2 and abs(my - y) <= CARD_H / 2:
                return k

    def pick_start(self, e):
        k = self.hit(e)
        if k:
            self.start.set(k)
            self.build()

    def pick_target(self, e):
        k = self.hit(e)
        if k:
            self.target.set(NONE if k == self.target.get() else k)
            self.build()

    # ---------- running BFS ----------
    def build(self):
        self.stop()
        start = self.start.get()
        if start not in self.g.adj:
            start = self.g.people[0]
            self.start.set(start)
        tgt = self.target.get()
        tgt = None if tgt in (NONE, "") or tgt not in self.g.adj else tgt
        desc = self.order.get() == "Descending"
        self.steps = build_steps(start, desc, tgt, self.g.adj)
        last = self.steps[-1]
        full = build_steps(start, desc, None, self.g.adj)[-1]
        self.full_work = max(1, full["shift"] + full["cmp"])
        self.final_work = last["shift"] + last["cmp"]
        self.idx = 0
        self.card(tgt, last)
        self.render()

    def card(self, tgt, last):
        """Fill the case card for the current scenario / start / target."""
        pct = 100 * self.final_work / self.full_work
        if tgt is None:
            self.badge.config(text="FULL TRAVERSAL", bg=GREEN_DARK, fg="white")
        else:
            case = classify(pct)
            self.badge.config(text=f"{case} CASE", bg=CASE_COLOR[case], fg="#12211a")
        if self.sc:
            changed = (self.start.get(), tgt or "") != (self.sc["start"], self.sc["target"])
            self.ttl.config(text=self.sc["title"] + ("  (start/target changed)"
                                                     if changed else ""))
            self.ex.config(text="Real life: " + self.sc["example"])
            self.why.config(text="Why: " + self.sc["why"])
        elif self.scn.get() == DEMO:
            self.ttl.config(text="A-I graph")
            self.ex.config(text="Left-click a node to set the start, right-click a "
                                "node to set a target.")
            self.why.config(text="")
        else:
            self.ttl.config(text=self.scn.get())
            self.ex.config(text="Your own family tree. Choose start and target to see "
                                "whether the search is a best, average or worst case.")
            self.why.config(text="")

    def draw_meter(self, s):
        work = s["shift"] + s["cmp"]
        pct = 100 * work / self.full_work
        m = self.meter
        m.delete("all")
        case = classify(pct) if s["target"] else None
        m.create_rectangle(0, 0, METER_W, 12, fill=GREEN_SOFT, outline="")
        m.create_rectangle(0, 0, METER_W * min(pct, 100) / 100, 12,
                           fill=CASE_COLOR.get(case, GREEN), outline="")
        for mark in (20, 80):                         # best / worst boundaries
            m.create_line(METER_W * mark / 100, 0, METER_W * mark / 100, 12, fill=INK)
        end = self.idx == len(self.steps) - 1
        text = (f"Work so far: {work} of {self.full_work} operations "
                f"(shifts + comparisons) = {pct:.0f}% of a full traversal")
        if end and s["target"]:
            text += f"  ->  {classify(pct)} case"
        self.meter_lbl.config(text=text)

    # ---------- drawing ----------
    def edge_points(self, a, b):
        """Square connector: down from the upper card, across, down into the lower card.
        Two cards in the same row (partners) just get a straight line."""
        xa, ya = self.at(a)
        xb, yb = self.at(b)
        if ya == yb:
            return [xa, ya, xb, yb]
        if ya > yb:                                   # make a the upper card
            xa, ya, xb, yb = xb, yb, xa, ya
        start_y = ya + CARD_H / 2                     # bottom of the upper card
        end_y = yb - CARD_H / 2                       # top of the lower card
        mid_y = (start_y + end_y) / 2
        return [xa, start_y, xa, mid_y, xb, mid_y, xb, end_y]

    def draw_card(self, k, s):
        """One person: white card, round avatar, name, and a tag for the special roles."""
        cv = self.cv
        x, y = self.at(k)
        w, h = CARD_W / 2, CARD_H / 2
        fill, outline, thick, ink = "white", BORDER, 1, INK
        if k in s["done"]:
            fill, outline = GREEN_SOFT, "#8fd9ac"
        if k in s["q"]:
            fill, outline = "#eaf4ff", "#7fb6ee"
        if s["cur"] == k:
            fill, outline, thick = "#fff4e0", ORANGE, 3
        if k == s["target"]:                          # black card, like the "ex" cards in the design
            fill, ink = BLACK, "white"
        if s["found"] == k:
            outline, thick = GREEN, 3
        if k == self.start.get():                     # red outline, like the "That's you" card
            outline, thick = RED, 3

        cv.create_rectangle(x - w + 2, y - h + 4, x + w + 2, y + h + 4,
                            fill="#e1eae6", outline="")             # soft shadow
        cv.create_rectangle(x - w, y - h, x + w, y + h, fill=fill, outline=outline,
                            width=thick)
        draw_avatar(cv, x, y - 14, 30, k)
        cv.create_text(x, y + 33, text=k, fill=ink, font=f(9, True), width=CARD_W - 10)

        if k in s["dist"]:                            # distance from the start
            cv.create_rectangle(x + w - 31, y - h + 5, x + w - 5, y - h + 19,
                                fill=GREEN_DARK, outline="")
            cv.create_text(x + w - 18, y - h + 12, text=f"d={s['dist'][k]}",
                           fill="white", font=f(7, True))

        tag = None
        if s["found"] == k:
            tag = ("FOUND", GREEN_DARK, "white")
        elif k == self.start.get():
            tag = ("START", RED, "white")
        elif k == s["target"]:
            tag = ("TARGET", GOLD, "#12211a")
        if tag:
            cv.create_rectangle(x - 29, y + h - 8, x + 29, y + h + 8, fill=tag[1], outline="")
            cv.create_text(x, y + h, text=tag[0], fill=tag[2], font=f(7, True))

    def render(self):
        s = self.steps[self.idx]
        g, cv = self.g, self.cv
        W, H = g.size
        cw, ch = max(cv.winfo_width(), 1), max(cv.winfo_height(), 1)
        self.ox, self.oy = max(0, (cw - W) // 2), max(0, (ch - H) // 2)   # center small trees
        cv.config(scrollregion=(0, 0, max(cw, W), max(ch, H)))
        cv.delete("all")

        for a, b in g.edges:                          # every family link
            kind = self.kind(a, b)
            cv.create_line(*self.edge_points(a, b), fill=LINE,
                           width=3 if kind == "spouse" else 2,
                           dash=(3, 4) if kind == "sibling" else None)
        for a, b in s["tree"]:                        # links BFS has used
            cv.create_line(*self.edge_points(a, b), fill=GREEN, width=5)
        if s["act"]:                                  # the link BFS is looking at now
            cv.create_line(*self.edge_points(*s["act"]), fill=ORANGE, width=5)
        for k in g.pos:
            self.draw_card(k, s)

        self.code.config(state="normal")
        self.code.tag_remove("on", "1.0", "end")
        self.code.tag_add("on", f"{s['line'] + 1}.0", f"{s['line'] + 1}.end+1c")
        self.code.config(state="disabled")
        for k in self.sv:
            self.sv[k].config(text=str(s[k]))
        self.q_lbl.config(text="Queue (front first):  " + ("  ".join(s["q"]) or "empty"))
        self.o_lbl.config(text="Visit order:  " + ("  ".join(s["order"]) or "none yet"))
        self.note.config(text=s["note"])
        self.draw_meter(s)
        if self.idx == len(self.steps) - 1:
            self.stop()

    # ---------- playback ----------
    def go(self, d):
        self.idx = max(0, min(len(self.steps) - 1, self.idx + d))
        self.render()

    def tick(self):
        self.go(1)
        if self.job:
            self.job = self.after(1100 - self.speed.get() * 100, self.tick)

    def toggle(self):
        if self.job:
            return self.stop()
        if self.idx == len(self.steps) - 1:
            self.idx = 0
        self.play_btn.config(text="Pause")
        self.job = self.after(1, self.tick)

    def stop(self):
        if self.job:
            self.after_cancel(self.job)
            self.job = None
        self.play_btn.config(text="Play")

    def reset(self):
        self.stop()
        self.idx = 0
        self.render()

    # ---------- best / average / worst comparison table ----------
    def compare(self):
        desc = self.order.get() == "Descending"
        try:
            rows = evaluate_all(desc)
        except (OSError, ValueError, KeyError) as err:
            messagebox.showerror("Cannot compare", str(err))
            return
        win = tk.Toplevel(self)
        win.title("Best / average / worst case comparison")
        win.configure(bg=BG)
        tk.Label(win, bg=BG, fg=GREEN_DARK, font=f(14, True),
                 text=f"All family-tree scenarios ({'descending' if desc else 'ascending'}"
                      f" neighbor order)").pack(anchor="w", padx=12, pady=(10, 0))
        tk.Label(win, bg=BG, fg=MUTE, font=f(9), justify="left",
                 text="work = shifts + comparisons.  % = work compared with a full "
                      "traversal from the same start.  BEST <= 20%, WORST >= 80%."
                 ).pack(anchor="w", padx=12)
        cols = (("case", "Case", 80), ("title", "Scenario", 270), ("people", "People", 60),
                ("links", "Links", 55), ("route", "Start -> target", 130),
                ("found", "Found", 55), ("passes", "Passes", 55),
                ("comparisons", "Comparisons", 90), ("shifts", "Shifts", 55),
                ("work", "Work", 55), ("pct", "% of full", 70),
                ("measured", "Measured", 80))
        tree = ttk.Treeview(win, columns=[c[0] for c in cols], show="headings",
                            height=len(rows))
        for key, text, width in cols:
            tree.heading(key, text=text)
            tree.column(key, width=width, anchor="w" if key == "title" else "center")
        for case, color in CASE_COLOR.items():
            tree.tag_configure(case, foreground=color)
        for r in rows:
            tree.insert("", "end", tags=(r["measured"],), values=(
                r["case"], r["title"], r["people"], r["links"],
                f"{r['start']} -> {r['target']}", "yes" if r["found"] else "no",
                r["passes"], r["comparisons"], r["shifts"],
                f"{r['work']}/{r['full_work']}", f"{r['pct']}%", r["measured"]))
        tree.pack(padx=12, pady=8)

        def save():
            path = filedialog.asksaveasfilename(
                parent=win, defaultextension=".csv", initialfile="case_summary.csv",
                filetypes=[("CSV files", "*.csv")])
            if path:
                with open(path, "w", newline="", encoding="utf-8") as fh:
                    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
                    w.writeheader()
                    w.writerows(rows)
        ttk.Button(win, text="Save as CSV...", command=save).pack(
            anchor="e", padx=12, pady=(0, 10))


if __name__ == "__main__":
    App().mainloop()
