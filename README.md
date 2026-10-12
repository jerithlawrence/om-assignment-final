# PCB drill-head routing

This is my programming assignment for Optimization Methods.

**Name:** Lawrence Jerith

**Student ID:** MS26916026

I used the TSPLIB `pcb442` dataset to find a short route for a PCB drill head.
The head must visit all 442 drilling locations once and return to the starting
point. I modelled this as a Travelling Salesman Problem (TSP).

I compared two methods: Held–Karp dynamic programming for exact solutions on
small subsets, and nearest neighbour followed by 2-opt local search for larger
subsets and the full dataset.

## Dataset

I downloaded the dataset on 12 October 2026 from the
[official TSPLIB server](https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/pcb442.tsp.gz).

The original file was compressed. I extracted it and saved it without changing
its contents as `dataset/pcb442.tsp`. The scripts read this local file, so they
do not download the dataset again.

The dataset uses the `EUC_2D` distance rule. For each pair of locations, I
calculate the Euclidean distance and round it using
`floor(Euclidean distance + 0.5)`. Each edge is rounded separately before adding
up the tour distance. The distance also includes the return to the start.

## How to run

Use Python 3.12. I used Python 3.12.14 for the saved results.

Run these commands from the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/verify.py
python scripts/main.py
```

The scripts find the dataset and output folder relative to the project, so
calling a script by its path also works from another folder. Running `main.py`
replaces the existing results and figures in `output/`.

The experiments run one after another. Once the dependencies are installed,
no internet connection, separate optimization solver or API key is needed.
A run can take seconds to minutes, depending on the computer. Runtime will
vary, but using the fixed NumPy version in `requirements.txt` and the same
seeds reproduces the routes and integer distances.

## Methods and experiments

### Exact method

I used Held–Karp dynamic programming. It calculates every required state and
then works backwards to recover the shortest closed tour. Its time complexity
is O(n²2ⁿ), and its memory complexity is O(n2ⁿ). This growth makes it expensive
for large problems.

I tested it on 8, 10, 12, 14, 16 and 18 locations, repeating each size three
times to measure runtime. The function accepts at most 20 locations to avoid
excessive memory use and long runs. It has no time limit and does not use an
external solver.

### Heuristic method

I started at a random location chosen using a fixed seed. Nearest neighbour
then builds a tour by choosing the closest unvisited location each time.
After that, 2-opt checks possible pairs of edges and makes the change that
reduces the distance the most. It stops when no 2-opt change can improve the
tour.

I used seeds 0–9 at every problem size. This method was tested on the same
small subsets as Held–Karp, and on 50, 100, 200 and all 442 locations. If
nearest-neighbour distances are equal, the smaller node index is chosen.
If 2-opt improvements are equal, the first edge pair in row-major order is
chosen, meaning pairs are checked by their first index and then their second.

### Comparing the methods

I used NumPy `default_rng(2026)` to choose the subsets. They are nested, so
each larger subset includes the locations in the smaller ones. Both methods
receive exactly the same subset at each small size. For the full dataset,
I kept the original node order.

The measured runtime includes setting up the algorithm and building the route.
It does not include imports, reading the dataset, building the distance matrix,
checking the result or drawing the figures. I checked that every returned tour
visits each location exactly once and that its distance includes the return
edge. Where standard deviations are reported, they are sample standard
deviations.

### Correctness checks

`scripts/verify.py` checks the distance rounding, the return edge and rejection
of routes with repeated visits. It also compares Held–Karp with brute force on
separate small examples and checks that small 2-opt results have no improving
2-opt move left. These are correctness checks, separate from the experiments.

## Results

All 118 tours were feasible. For the 18-location subset, the exact optimum was
12,073, and Held–Karp took an average of 2.325445 seconds. All ten heuristic
runs also reached 12,073. This does not mean that the heuristic always finds
the optimum.

For the full 442-location dataset:

- Best heuristic distance: **52,205**, using seed 6.
- Mean distance across ten runs: **52,824.4**.
- Mean solve time per run: **0.150590 seconds**.
- Best gap from the published optimum of **50,778**: **2.8103%**.
- Total measured solver time for all ten runs: **1.505898 seconds**.

These timings came from the recorded run on macOS arm64 and will differ on
other computers. I used the published optimum as a reference; my exact method
did not solve the full dataset. I did not establish an optimum for the 50-,
100- or 200-location subsets, so I do not report optimality gaps for them.

## Project files

- `scripts/`: the dataset loader and experiment code, exact method, heuristic
  method and correctness checks.
- `dataset/pcb442.tsp`: the original extracted TSPLIB dataset.
- `output/results.csv`: the method, seed, distance, runtime and feasibility
  result for every run.
- `output/summary.csv`: the distance and runtime summaries.
- `output/routes.json`: every tour using the original TSPLIB node IDs, which
  start at 1. The first ID is not repeated at the end, but the return edge is
  included when calculating the distance.
- `output/experiment_details.json`: the selected node IDs, settings, software
  environment, source-file hashes and dataset SHA-256 hash.
- `output/convergence.csv`: the distance after each accepted improvement in
  the best full-dataset run.
- `output/*.png`: the five figures used in the report.
- `members.txt`: my name and student ID.
- `submission.txt`: the dataset, GitHub and YouTube links.
- `code_appendix.txt`: all four final Python scripts, separated by filename.

The DOCX report, PDF report and `Optimization-assignment.zip` are kept locally
and excluded from Git. The ZIP contains both report formats. The complete
source code is also included in the report appendix.

## Limitations

I treated the problem as a symmetric, closed TSP. The model does not include
machine movement dynamics, tool changes, obstacles or drilling time. The
coordinates are in dataset units; I have not assumed that they are millimetres.

I tested one set of nested subsets and ten starting seeds at each size. These
results describe those runs and are not enough to make general statistical
claims about other boards or all possible starting points.

## References

- [TSPLIB EUC_2D specification, Section 2.1](https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/tsp95.pdf)
- [Official TSPLIB optimum values](https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/TSP-BEST.html)
- [Held and Karp (1962)](https://doi.org/10.1137/0110015)
- [Croes (1958)](https://doi.org/10.1287/opre.6.6.791)

The dataset SHA-256 hash is:

```text
0f58bc2f1aa0023764ebc14b3b0dcb6e765ffe173963fdc1cb8443d969842b51
```

## Submission notes

The repository is private, so the assessor needs access to it. The YouTube
link is still `[To be added]`; I will add it after uploading the video.
The assignment brief asks for two members, but this submission lists only me.

I used AI assistance for the implementation, running the experiments and
drafting the report. This is also disclosed in the report. I am responsible
for the submission and viva, and I am not presenting the work as unaided or
claiming a second contributor.
