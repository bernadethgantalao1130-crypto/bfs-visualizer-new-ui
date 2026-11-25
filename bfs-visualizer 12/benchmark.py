"""Run every family-tree scenario in data/scenarios.csv and save the results.

    python benchmark.py

Writes results/case_summary.csv (ascending and descending neighbor order) and
prints a table. No GUI needed.
"""
import csv
from pathlib import Path

from bfs_core import evaluate_all

OUT = Path(__file__).resolve().parent / "results" / "case_summary.csv"


def main():
    rows = evaluate_all(False) + evaluate_all(True)
    for r in rows:
        r["matches_declared"] = "yes" if r["measured"] == r["case"] else "no"
    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    print(f"{'case':8}{'order':11}{'scenario':34}{'route':16}{'V':>3}{'E':>4}"
          f"{'work':>10}{'%':>8}  measured")
    for r in rows:
        route = f"{r['start']}->{r['target']}"
        print(f"{r['case']:8}{r['order']:11}{r['file'][:-4]:34}{route:16}"
              f"{r['people']:>3}{r['links']:>4}{r['work']:>5}/{r['full_work']:<4}"
              f"{r['pct']:>7}%  {r['measured']}")
    print(f"\nSaved {OUT}")


if __name__ == "__main__":
    main()
