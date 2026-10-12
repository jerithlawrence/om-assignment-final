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
python scripts/compare_models.py
```

`verify.py` checks rounding, route feasibility, exact results against brute
force, and small 2-opt results. `main.py` runs the experiments and replaces the
results and figures in `output/`. `compare_models.py` runs the full-board ILP
comparison with a five-minute solver limit. The PySCIPOpt wheel includes SCIP;
no internet connection is needed once dependencies are installed.

## Methods and experiments

- **Exact method:** Held–Karp dynamic programming finds a proven optimal tour.
  It is tested on 8, 10, 12, 14, 16 and 18 locations, with three runs per size.
  Its time complexity is O(n²2ⁿ) and memory complexity is O(n2ⁿ), so the
  function limits inputs to 20 locations.
- **Full-board exact model:** A binary ILP with SCIP adds constraints to
  prevent disconnected cycles. It starts from the seed-0 heuristic route.
  The saved status, lower bound and gap show whether optimality was proved;
  a time-limited feasible route is not automatically optimal.
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

All **118 tours in the original size study were feasible**. On the 18-location subset, the exact optimum
was **12,073**, with a mean Held–Karp runtime of **2.325445 seconds**. All ten
heuristic runs matched that optimum.

For the full 442-location dataset in that study:

| Measure | Result |
| --- | --- |
| Best heuristic distance | 52,205 (seed 6) |
| Mean distance over ten runs | 52,824.4 |
| Mean solve time per run | 0.150590 seconds |
| Published optimum | 50,778 |
| Best gap from the optimum | 2.8103% |

The separate full-board comparison found an ILP route of **50,778**, matching
the published optimum. SCIP reached its time limit with a lower bound of
50,737 and a 0.0808% solver gap, so this run did not independently prove
optimality. Total ILP runtime was 301.533 seconds; ten fresh heuristic runs
took 2.514 seconds together, with the same best distance of 52,205. All 11
routes were feasible. Complete paired routes, timings and solver evidence
are saved in `output/full_comparison.json` and the comparison figures/tables.

No optimum is claimed for the 50-, 100- or 200-location subsets. Timings were
measured on macOS arm64 and vary by computer. Use
`python scripts/compare_models.py --plots-only` to redraw saved comparisons.

## Project files

- `scripts/`: exact method, heuristic, experiments and correctness checks.
- `dataset/`: the original benchmark file.
- `output/`: per-run results, summary tables, saved routes, experiment settings,
  improvement history and route-comparison figures.
- `requirements.txt`: fixed dependency versions.
- `members.txt` and `submission.txt`: student details and submission links.
- `code_appendix.txt`: all six Python scripts in full.

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
- [PySCIPOpt](https://pyscipopt.readthedocs.io/)
