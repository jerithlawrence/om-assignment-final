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

Use Python 3.12. Install the pinned dependencies in `requirements.txt`.
The experimental pipeline and full results will be added after validation.

The report and submission ZIP are excluded from version control.
