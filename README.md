# PCB drill-head routing

Optimization Methods programming assignment by Lawrence Jerith (MS26916026).
The task is a closed travelling salesman tour through TSPLIB pcb442.
The exact approach is Held–Karp dynamic programming on small subsets; the
heuristic is nearest-neighbour construction with a seeded random start,
followed by best-improvement 2-opt local search.

## Dataset

Original source: https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/pcb442.tsp.gz

`dataset/pcb442.tsp` is the original decompressed file, downloaded on
12 October 2026. Its 442 coordinates describe a drilling problem and use
EUC_2D integer distances: floor(Euclidean distance + 0.5), rounded per edge.
Execution reads this local file and does not need network access.

## Setup

Use Python 3.12 (the recorded run used 3.12.14):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/verify.py
python scripts/main.py
```

Paths are resolved relative to the project, so execution also works from a
different current directory. The pipeline overwrites the files in `output/`.
It runs serially and needs no solver installation, internet access or API key.
The experiment takes seconds to minutes depending on the host. Timings vary;
with the pinned NumPy version the seeded routes and integer costs reproduce.

## Methods and experiment

- Held–Karp dynamic programming completes all states and reconstructs an
  optimal closed tour. Time is O(n²2ⁿ), space O(n2ⁿ). The experiment uses
  8, 10, 12, 14, 16 and 18 nodes, three timing repetitions each. The function
  limits inputs to 20 nodes to protect resources. No external solver or
  time limit is used.
- Local search constructs a nearest-neighbour tour from a seeded random
  start, then applies best-improvement 2-opt until no improving move remains.
  Seeds 0–9 are used at each size, including 50, 100, 200 and 442 nodes.
  Ties use smallest node index, then the first row-major edge pair.
- Small instances are nested random subsets from NumPy `default_rng(2026)`.
  Both methods use identical subsets. The full instance uses original order.
- Runtime includes the solver's initialization and route construction, but
  excludes imports, loading, distance construction, validation and plotting.
  Every returned route is checked for unique coverage and closed-tour cost.
  All statistics use sample standard deviations where applicable.

`verify.py` checks half-up rounding, closure, rejection of duplicate visits,
exact agreement with brute force on independent small examples, and local
optimality of small 2-opt outputs. It is a correctness test, not another
experimental method.

## Recorded results

All 118 tours were feasible. At 18 nodes the exact optimum was 12,073 and
Held–Karp averaged 2.325445 seconds. All ten heuristic runs matched that value;
this does not establish a general optimality guarantee for the heuristic.

For all 442 nodes, the best heuristic cost was **52,205** (seed 6), the mean
was **52,824.4**, and mean solve time was **0.150590 seconds** per run.
The best gap was **2.8103%** relative to the published optimum of **50,778**.
Ten full runs took 1.505898 seconds in summed solver time. These are recorded
macOS arm64 timings, not guaranteed performance. The published optimum was
not computed by this implementation. No optimum or gap is claimed for the
50-, 100- or 200-node subsets.

## Files

- `scripts/`: dataset/experiment pipeline, exact method, heuristic, verification.
- `dataset/pcb442.tsp`: unmodified decompressed official benchmark.
- `output/results.csv`: every solve, seed, objective, runtime and feasibility.
- `output/summary.csv`: aggregated quality and timing statistics.
- `output/routes.json`: all tours in original one-based TSPLIB IDs; the
  first ID is not repeated, but the last-to-first edge is always included.
- `output/experiment_details.json`: exact subset IDs, settings, environment,
  source hashes and dataset SHA-256.
- `output/convergence.csv`: accepted-move costs for the best full run.
- `output/*.png`: the five final figures used in the report.
- `members.txt`, `submission.txt`, `code_appendix.txt`: submission records.

The DOCX and PDF reports and `Optimization-assignment.zip` are local
submission artifacts, excluded from Git. The ZIP includes both report formats.
The code appendix reproduces the four final scripts, separated by filenames.

## Interpretation and references

This is a symmetric closed TSP distance model, without machine dynamics,
tool changes, obstacles or drilling times. Coordinates are dataset units,
not assumed physical millimetres. Only one nested subset family is evaluated;
ten starts are descriptive evidence, not a statistical generalization.

- TSPLIB EUC_2D specification, Section 2.1:
  https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/tsp95.pdf
- Official optimum listing:
  https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/TSP-BEST.html
- Held and Karp (1962): https://doi.org/10.1137/0110015
- Croes (1958): https://doi.org/10.1287/opre.6.6.791

Dataset SHA-256:
`0f58bc2f1aa0023764ebc14b3b0dcb6e765ffe173963fdc1cb8443d969842b51`.

The repository is private; the assessor needs repository access. The video
link remains `[To be added]` as requested. The supplied brief requests two
members; this submission lists only the specified member. AI assistance
supported implementation, experiment execution and report drafting, as
disclosed in the report. Submission and viva responsibility remain with the
named student; no unaided authorship or second contributor is claimed.
