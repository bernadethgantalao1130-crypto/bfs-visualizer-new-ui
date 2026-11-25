# BFS Visualizer (Python)

Step-by-step breadth-first search with a purple theme, live code highlighting,
and counters for passes, comparisons, and shifts. Now with family-tree
scenarios that show the **best, average and worst case** of BFS.

## Run
    python main.py          # the visualizer
    python benchmark.py     # no GUI: runs all scenarios, writes results/case_summary.csv

Uses only the standard library (tkinter). On Linux you may need:
    sudo apt install python3-tk

## Files
- main.py        the tkinter window
- bfs_core.py    the BFS logic, CSV loading and family-tree layout (no GUI)
- benchmark.py   runs every scenario and saves the results as CSV
- data/          the 12 family-tree CSV files + scenarios.csv (the index)
- results/       case_summary.csv written by benchmark.py

## Controls
Pick a **Scenario**, then Back / Step / Play / Reset and the speed slider.
Left-click a node to set the start, right-click a node to set the target.
Choose ascending or descending neighbor order.
**Load CSV...** opens your own family tree. **Compare all cases** shows a table
of every scenario and can save it as CSV.

## Reading the tree
Every person is a card with a round avatar. Square connector lines go from
parents down to children; partners sit side by side.

| What you see                 | Meaning                                   |
|------------------------------|-------------------------------------------|
| Red outline + START tag      | the start node (left-click to change)     |
| Black card + TARGET tag      | the target node (right-click to change)   |
| Black card + green FOUND tag | BFS reached the target                    |
| Orange outline               | the node BFS is expanding right now       |
| Blue card                    | waiting in the queue                      |
| Green card                   | already expanded (visited)                |
| Green line / orange line     | links BFS has used / link it checks now   |
| d=N badge                    | number of links from the start            |

Big families are drawn at full size: use the scroll bars or the mouse wheel
(hold Shift to scroll sideways).

## The 12 scenarios (data/)
| Case    | File                           | Real-life example                          | Start -> target |
|---------|--------------------------------|--------------------------------------------|-----------------|
| BEST    | best_1_nuclear_family.csv      | Mom looks for her daughter at home         | Maria -> Lia    |
| BEST    | best_2_grandpa_reunion.csv     | Grandpa calls his son at a reunion         | Ramon -> Carlos |
| BEST    | best_3_big_household.csv       | Dad asks for his eldest child              | Arman -> Cris   |
| AVERAGE | avg_1_cousin_reunion.csv       | Finding a first cousin                     | Eli -> Hugo     |
| AVERAGE | avg_2_wedding_two_families.csv | Two families meet at a wedding             | Carl -> Hector  |
| AVERAGE | avg_3_four_generations.csv     | Finding a second cousin on a family site   | Lou -> Quin     |
| AVERAGE | avg_4_great_aunt.csv           | Finding grandma's sister for a photo       | Xavi -> Rosa    |
| AVERAGE | avg_5_blended_family.csv       | Meeting a new stepbrother                  | Sal -> Vic      |
| WORST   | worst_1_deep_lineage.csv       | Tracing ancestry back 8 generations        | Hugo -> Ansel   |
| WORST   | worst_2_unrelated_person.csv   | Searching for someone who is not related   | Rey -> Zed      |
| WORST   | worst_3_large_clan.csv         | The newest baby of a large clan            | Hal -> Zed      |
| WORST   | worst_4_missing_from_registry.csv | A name missing from the family registry | Aldo -> Zara    |

## What "best / average / worst" means here
BFS time is O(V + E): V people, E family links. Work = shifts + comparisons;
a full traversal costs V + 2E. The app compares the work of the search with
that full traversal:

- BEST     <= 20% : the target is a close relative, found in the first pass(es).
- AVERAGE  20-80% : the target is a few links away, about half the family is explored.
- WORST    >= 80% : the target is the deepest relative or not connected at all,
                    so almost the whole family (or all of it) is explored.

## CSV format
One file per family, header `person_a,person_b,relation`:

    Maria,Tomas,spouse      Maria and Tomas are partners
    Maria,Lia,parent        Maria is a parent of Lia (parent -> child)
    Ana,Ben,sibling         Ana and Ben are siblings (optional)
    Zara,,                  a person with no relatives (leave the other two columns empty)

Lines starting with # are ignored. Keep names short (6 letters fit best).
The layout is automatic: parents on top, children below, partners side by side.
To add a scenario, add its CSV to data/ and a row to data/scenarios.csv
(file, case, title, example, start, target, why).
