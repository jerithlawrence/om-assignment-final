"""Reproduce the pcb442 experiments and figures from the local dataset."""

import csv
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from exact_method import held_karp
from heuristic_method import local_search, tour_length

ROOT = Path(__file__).resolve().parents[1]
SIZES = (8, 10, 12, 14, 16, 18, 50, 100, 200, 442)
SEEDS = tuple(range(10))
SUBSET_SEED = 2026
EXACT_REPEATS = 3
FULL_OPTIMUM = 50778  # Published by TSPLIB; not computed by our exact solver.


def load_dataset(path):
    """Read and validate the original TSPLIB coordinate file."""
    metadata, rows = {}, []
    coordinates = False
    for line in path.read_text().splitlines():
        line = line.strip()
        if line == "NODE_COORD_SECTION":
            coordinates = True
        elif line == "EOF":
            break
        elif coordinates and line:
            node, x, y = line.split()
            rows.append((int(node), float(x), float(y)))
        elif ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()
    if (metadata.get("NAME") != "pcb442"
            or metadata.get("TYPE") != "TSP"
            or metadata.get("EDGE_WEIGHT_TYPE") != "EUC_2D"
            or int(metadata.get("DIMENSION", 0)) != 442
            or len(rows) != 442):
        raise ValueError("Expected original pcb442 EUC_2D data")
    if [row[0] for row in rows] != list(range(1, 443)):
        raise ValueError("Expected unique consecutive TSPLIB node IDs")
    xy = np.array([row[1:] for row in rows])
    if not np.isfinite(xy).all():
        raise ValueError("Coordinates must be finite")
    return metadata, xy


def distance_matrix(xy):
    """TSPLIB EUC_2D uses nearest integer, with halves rounded upward."""
    difference = xy[:, None, :] - xy[None, :, :]
    return np.floor(np.sqrt((difference ** 2).sum(axis=2)) + 0.5
                    ).astype(np.int64)


def validate_tour(route, distance, expected):
    if sorted(route) != list(range(len(distance))):
        raise ValueError("Tour must visit every node exactly once")
    if tour_length(route, distance) != expected:
        raise ValueError("Closed-tour cost does not match")


def write_csv(path, rows):
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows):
    summary = []
    for n in SIZES:
        for method in ("held_karp", "two_opt"):
            group = [r for r in rows if r["n"] == n
                     and r["method"] == method]
            if not group:
                continue
            costs = [r["distance"] for r in group]
            times = [r["runtime_seconds"] for r in group]
            reference = group[0]["reference_distance"]
            summary.append(dict(
                n=n, method=method, runs=len(group), best=min(costs),
                mean=float(np.mean(costs)), worst=max(costs),
                sd=float(np.std(costs, ddof=1)),
                mean_seconds=float(np.mean(times)),
                sd_seconds=float(np.std(times, ddof=1)),
                reference_distance=reference,
                mean_gap_percent=(100 * (np.mean(costs) / reference - 1)
                                  if reference else ""),
                feasible_runs=sum(r["feasible"] for r in group)))
    return summary


def figures(xy, rows, summary, best_route, history, output):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False})

    def save(name):
        plt.savefig(output / name, dpi=180, bbox_inches="tight")
        plt.close()

    for name, title, route in (
            ("drilling_locations.png", "pcb442 drilling locations", None),
            ("optimized_route.png", "Best 2-opt closed tour", best_route)):
        fig, ax = plt.subplots(figsize=(7, 6))
        if route is not None:
            closed = np.append(route, route[0])
            ax.plot(xy[closed, 0], xy[closed, 1], lw=0.8, color="#28638a")
            ax.scatter(*xy[route[0]], s=65, marker="s", color="#c44b28",
                       label="Start / return", zorder=3)
            ax.legend()
        ax.scatter(xy[:, 0], xy[:, 1], s=6, color="#172e40")
        ax.set(title=title, xlabel="x (dataset units)",
               ylabel="y (dataset units)", aspect="equal")
        save(name)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for method, label in (("held_karp", "Held–Karp"),
                          ("two_opt", "NN + 2-opt")):
        group = [r for r in summary if r["method"] == method]
        axes[0].plot([r["n"] for r in group],
                     [r["mean_seconds"] for r in group], "o-", label=label)
    axes[0].set(xscale="log", yscale="log", xlabel="Locations (log scale)",
                ylabel="Mean solve time (s, log scale)")
    axes[0].legend()
    small = [r for r in summary if r["method"] == "two_opt" and r["n"] <= 18]
    axes[1].bar([str(r["n"]) for r in small],
                [r["mean_gap_percent"] for r in small], color="#28638a")
    axes[1].set(xlabel="Locations", ylabel="Mean gap to exact optimum (%)")
    fig.tight_layout()
    save("algorithm_comparison.png")
    full = [r for r in rows if r["n"] == 442]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(SEEDS, [r["initial_distance"] for r in full], "o-", label="Initial NN")
    ax.plot(SEEDS, [r["distance"] for r in full], "o-", label="After 2-opt")
    ax.axhline(FULL_OPTIMUM, color="#c44b28", ls="--", label="Published optimum")
    ax.set(xlabel="Random seed", ylabel="Closed-tour distance", xticks=SEEDS)
    ax.legend()
    save("full_benchmark_runs.png")
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.plot(range(len(history)), history, color="#28638a")
    ax.axhline(FULL_OPTIMUM, color="#c44b28", ls="--", label="Published optimum")
    ax.set(xlabel="Accepted 2-opt moves (best full run)",
           ylabel="Closed-tour distance")
    ax.legend()
    save("convergence.png")


def main():
    output = ROOT / "output"
    output.mkdir(exist_ok=True)
    dataset = ROOT / "dataset" / "pcb442.tsp"
    metadata, xy = load_dataset(dataset)
    full_distance = distance_matrix(xy)
    order = np.random.default_rng(SUBSET_SEED).permutation(len(xy))
    rows, routes, subsets = [], {}, {}
    best_full, best_history, best_cost = None, None, float("inf")
    started = datetime.now(timezone.utc).isoformat()
    for n in SIZES:
        # Nested subsets; full instance retains the original TSPLIB order.
        indices = np.sort(order[:n]) if n < 442 else np.arange(442)
        subsets[str(n)] = (indices + 1).tolist()
        d = full_distance[np.ix_(indices, indices)]
        reference = FULL_OPTIMUM if n == 442 else None
        jobs = ([('held_karp', run) for run in range(EXACT_REPEATS)]
                if n <= 18 else [])
        jobs += [('two_opt', seed) for seed in SEEDS]
        for method, run in jobs:
            start = perf_counter()
            if method == "held_karp":
                route, cost = held_karp(d)
                initial, history = None, []
            else:
                route, initial, history = local_search(d, run)
                cost = history[-1]
            elapsed = perf_counter() - start
            validate_tour(route, d, cost)
            if method == "held_karp":
                reference = cost
            if reference is not None and cost < reference:
                raise ValueError("Cost is below verified reference")
            key = f"{n}_{method}_{run}"
            routes[key] = (indices[route] + 1).tolist()
            rows.append(dict(
                n=n, method=method, run=run,
                seed=run if method == "two_opt" else "",
                distance=cost, initial_distance=initial,
                runtime_seconds=elapsed, feasible=True,
                status="optimal" if method == "held_karp" else "local_optimum",
                reference_distance=reference,
                gap_percent=100 * (cost / reference - 1) if reference else "",
                accepted_moves=len(history) - 1 if history else ""))
            if n == 442 and cost < best_cost:
                best_full, best_history, best_cost = route.copy(), history, cost
        print(f"Completed n={n}", flush=True)
    summary = summarize(rows)
    write_csv(output / "results.csv", rows)
    write_csv(output / "summary.csv", summary)
    write_csv(output / "convergence.csv",
              [dict(move=i, distance=c) for i, c in enumerate(best_history)])
    (output / "routes.json").write_text(json.dumps(routes, indent=2) + "\n")
    details = dict(
        started_utc=started, python=sys.version, platform=platform.platform(),
        machine=platform.machine(), numpy=np.__version__,
        matplotlib=matplotlib.__version__, dataset=metadata,
        dataset_sha256=hashlib.sha256(dataset.read_bytes()).hexdigest(),
        source_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in sorted((ROOT / "scripts").glob("*.py"))},
        subset_seed=SUBSET_SEED, subset_node_ids=subsets, seeds=SEEDS,
        exact_repeats=EXACT_REPEATS, exact_limit=18,
        heuristic="random-start NN, best-improvement 2-opt until no gain",
        tie_breaking="smallest node index / first row-major edge pair",
        timing="perf_counter; solver only, including initialization; serial",
        published_full_optimum=FULL_OPTIMUM,
        reference_url="https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/"
                      "tsp/TSP-BEST.html")
    (output / "experiment_details.json").write_text(
        json.dumps(details, indent=2) + "\n")
    figures(xy, rows, summary, best_full, best_history, output)
    print(f"Best full tour: {best_cost}; all {len(rows)} tours feasible")


if __name__ == "__main__":
    main()
