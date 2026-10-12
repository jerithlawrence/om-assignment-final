# PCB drill-head routing

**Lawrence Jerith — MS26916026**

This project finds a short route through the 442 drilling locations in TSPLIB
`pcb442`. The drill head visits each location once and returns to the start,
which makes this a closed Travelling Salesman Problem (TSP).

## Dataset

The [official TSPLIB dataset](https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/pcb442.tsp.gz)
is extracted without changes into `dataset/pcb442.tsp`. The scripts load this
local file without downloading it again.

Distances follow the TSPLIB `EUC_2D` rule:
`floor(Euclidean distance + 0.5)`. Each edge is rounded separately, and the
return edge is included in the total.

## How to run

Use Python 3.12 and run these commands from the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/verify.py
python scripts/main.py
```

`verify.py` checks rounding, route feasibility, exact results against brute
force, and small 2-opt results. `main.py` runs the experiments and replaces the
results and figures in `output/`. No separate solver or internet connection
is needed after installing the dependencies.

## Methods and experiments

- **Exact method:** Held–Karp dynamic programming finds a proven optimal tour.
  It is tested on 8, 10, 12, 14, 16 and 18 locations, with three runs per size.
  Its time complexity is O(n²2ⁿ) and memory complexity is O(n2ⁿ), so the
  function limits inputs to 20 locations.
- **Heuristic:** Nearest neighbour builds a route from a seeded random start.
  Best-improvement 2-opt then shortens it until no improving 2-opt move remains.
  Seeds 0–9 are tested on the same small subsets and on 50, 100, 200 and all
  442 locations. These results are not guaranteed to be globally optimal.

Both methods use the same nested subsets, selected with NumPy
`default_rng(2026)`; 2026 is the random seed. Runtime includes algorithm setup
and route construction, but excludes loading, distance-matrix construction,
validation and plotting. Every route is checked for unique visits and the
correct closed-tour distance. Full settings and software versions are saved
in `output/experiment_details.json`.

## Results

All **118 tours were feasible**. On the 18-location subset, the exact optimum
was **12,073**, with a mean Held–Karp runtime of **2.325445 seconds**. All ten
heuristic runs matched that optimum.

For the full 442-location dataset:

| Measure | Result |
| --- | --- |
| Best heuristic distance | 52,205 (seed 6) |
| Mean distance over ten runs | 52,824.4 |
| Mean solve time per run | 0.150590 seconds |
| Published optimum | 50,778 |
| Best gap from the optimum | 2.8103% |

The full-instance optimum is a published reference, not a result from this
exact implementation. No optimality gap is reported for the 50-, 100- or
200-location subsets. Timings were measured on macOS arm64 and vary by
computer.

## Project files

- `scripts/`: exact method, heuristic, experiments and correctness checks.
- `dataset/`: the original benchmark file.
- `output/`: per-run results, summary tables, saved routes, experiment settings,
  improvement history and five report figures.
- `requirements.txt`: fixed dependency versions.
- `members.txt` and `submission.txt`: student details and submission links.
- `code_appendix.txt`: all four Python scripts in full.

The DOCX and PDF reports are included in the local submission ZIP and excluded
from Git.

## Limitations

The model uses distance only. It does not include machine dynamics, tool
changes, obstacles or drilling time, and dataset units are not assumed to be
millimetres. One nested subset family and ten starts per size give a limited
comparison, so the findings should not be generalised to every board.

## References

- [TSPLIB distance specification, Section 2.1](https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/tsp95.pdf)
- [Official TSPLIB optimum values](https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/TSP-BEST.html)
- [Held and Karp — dynamic programming](https://doi.org/10.1137/0110015)
- [Croes — travelling salesman local search](https://doi.org/10.1287/opre.6.6.791)
