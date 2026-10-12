"""Run the full-board ILP comparison and plot saved complete tours."""

import argparse
import csv
import hashlib
import json
import platform
from time import perf_counter

import matplotlib.pyplot as plt
import numpy as np
import pyscipopt

from exact_method import held_karp
from heuristic_method import local_search
from ilp_method import solve_ilp
from main import (FULL_OPTIMUM, ROOT, SEEDS, distance_matrix, load_dataset,
                  validate_tour, write_csv)


def draw_pair(xy, routes, titles, path):
    """Draw every location and edge on identical axes; arrows show direction."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 6.7), sharex=True, sharey=True)
    for ax, route, title in zip(axes, routes, titles):
        route = np.asarray(route)
        route = np.roll(route, -int(np.where(route == 0)[0][0]))
        closed = np.append(route, route[0])
        points = xy[closed]
        ax.plot(points[:, 0], points[:, 1], color="#28638a", lw=0.75)
        ax.scatter(xy[:, 0], xy[:, 1], s=8, color="#172e40", zorder=3)
        ax.scatter(*xy[0], marker="s", s=40, color="#c44b28",
                   label="Common start / return", zorder=4)
        for k in range(0, len(route), max(1, len(route) // 12)):
            a, b = points[k], points[k + 1]
            ax.annotate("", xy=b, xytext=a,
                        arrowprops=dict(arrowstyle="->", color="#c44b28",
                                        lw=0.9, mutation_scale=9))
        ax.set(title=title, xlabel="x (dataset units)", aspect="equal")
        ax.legend(loc="upper left", fontsize=8)
    axes[0].set_ylabel("y (dataset units)")
    fig.tight_layout()
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def edge_set(route):
    return {tuple(sorted((int(a), int(b))))
            for a, b in zip(route, np.roll(route, -1))}


def export_comparison(record, xy, distance, output):
    runs = record["runs"]
    exact = runs[0]
    heuristic = min(runs[1:], key=lambda r: r["distance"])
    best = [exact, heuristic]
    routes = [np.array(r["node_ids"]) - 1 for r in best]
    for route, result in zip(routes, best):
        validate_tour(route, distance, result["distance"])
    common = len(edge_set(routes[0]) & edge_set(routes[1]))
    summary = []
    for route, result, group in zip(routes, best, [runs[:1], runs[1:]]):
        lengths = distance[route, np.roll(route, -1)]
        summary.append(dict(
            method=result["method"], runs=len(group),
            best_distance=result["distance"],
            mean_distance=float(np.mean([r["distance"] for r in group])),
            best_run_seconds=result["runtime_seconds"],
            mean_seconds=float(np.mean([r["runtime_seconds"] for r in group])),
            total_seconds=sum(r["runtime_seconds"] for r in group),
            best_seed=result.get("seed", ""), status=result["status"],
            lower_bound=result.get("lower_bound", ""),
            solver_gap=result.get("solver_gap", ""),
            reference_gap_percent=100 * (result["distance"] / FULL_OPTIMUM - 1),
            visited_nodes=len(set(route)), edges=len(route),
            mean_edge=float(np.mean(lengths)), longest_edge=int(max(lengths)),
            shared_edges=common))
    write_csv(output / "best_model_comparison.csv", summary)
    status = "proven optimal" if exact["status"] == "optimal" else "not proven optimal"
    titles = [f"Exact ILP model ({status})\nDistance {exact['distance']:,}",
              f"Best NN + 2-opt (seed {heuristic['seed']})\n"
              f"Distance {heuristic['distance']:,}"]
    draw_pair(xy, routes, titles, output / "complete_routes_comparison.png")
    old = list(csv.DictReader((output / "results.csv").open()))
    saved = json.loads((output / "routes.json").read_text())
    subsets = json.loads((output / "experiment_details.json").read_text())
    small = []
    for n in (8, 10, 12, 14, 16, 18):
        group = [r for r in old if int(r["n"]) == n]
        e = next(r for r in group if r["method"] == "held_karp")
        hs = [r for r in group if r["method"] == "two_opt"]
        b = min(hs, key=lambda r: int(r["distance"]))
        small.append(dict(
            n=n, exact_distance=int(e["distance"]),
            heuristic_best=int(b["distance"]),
            excess=int(b["distance"]) - int(e["distance"]),
            best_gap_percent=100 * (int(b["distance"]) / int(e["distance"]) - 1),
            exact_mean_seconds=float(np.mean([float(r["runtime_seconds"])
                                              for r in group if r["method"] == "held_karp"])),
            heuristic_total_seconds=sum(float(r["runtime_seconds"]) for r in hs)))
        if n == 10:
            ids = subsets["subset_node_ids"]["10"]
            small_routes = [[ids.index(v) for v in saved[f"10_{r['method']}_{r['run']}"]]
                            for r in [e, b]]
            draw_pair(xy[np.array(ids) - 1], small_routes,
                      [f"Held–Karp optimum: {e['distance']}",
                       f"Best NN + 2-opt: {b['distance']}"],
                      output / "subset_routes_comparison.png")
    write_csv(output / "best_subset_comparison.csv", small)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plots-only", action="store_true")
    args = parser.parse_args()
    output = ROOT / "output"
    _, xy = load_dataset(ROOT / "dataset" / "pcb442.tsp")
    distance = distance_matrix(xy)
    path = output / "full_comparison.json"
    if args.plots_only:
        record = json.loads(path.read_text())
    else:
        # Cross-check the ILP on independent small cases, including subtours.
        for n in (4, 6, 8, 10):
            sample = np.random.default_rng(n).uniform(0, 100, (n, 2))
            d = distance_matrix(sample)
            route, evidence = solve_ilp(d, time_limit=30)
            _, optimum = held_karp(d)
            validate_tour(route, d, optimum)
            assert evidence["status"] == "optimal"
        d = np.full((6, 6), 10, dtype=int)
        d[:3, :3] = d[3:, 3:] = 1
        np.fill_diagonal(d, 0)
        route, evidence = solve_ilp(d, time_limit=30)
        validate_tour(route, d, 24)
        assert evidence["status"] == "optimal"
        print("ILP checks passed; solving all 442 nodes...", flush=True)
        route, evidence = solve_ilp(distance, time_limit=300)
        runs = [dict(method="ilp", **evidence, node_ids=(route + 1).tolist())]
        print(f"ILP: {evidence['distance']}, {evidence['status']}", flush=True)
        for seed in SEEDS:
            start = perf_counter()
            route, initial, history = local_search(distance, seed)
            elapsed = perf_counter() - start
            validate_tour(route, distance, history[-1])
            runs.append(dict(method="two_opt", seed=seed,
                             distance=history[-1], initial_distance=initial,
                             runtime_seconds=elapsed, status="local_optimum",
                             node_ids=(route + 1).tolist()))
        record = dict(
            runs=runs, platform=platform.platform(), python=platform.python_version(),
            numpy=np.__version__, pyscipopt=pyscipopt.__version__,
            source_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in sorted((ROOT / "scripts").glob("*.py"))},
            dataset_sha256=hashlib.sha256((ROOT / "dataset/pcb442.tsp").read_bytes()).hexdigest(),
            settings=dict(threads=1, randomseedshift=0, relative_gap=0,
                          feasibility_tolerance=1e-6, strong_dual_reductions=False,
                          time_limit_seconds=300, warm_start="seed-0 NN + 2-opt"),
            timing="Serial; model build, warm start, solve and route extraction included",
            verification="ILP agrees with Held–Karp on four independent cases; two triangles test passed")
        path.write_text(json.dumps(record, indent=2) + "\n")
    export_comparison(record, xy, distance, output)
    print("Saved full-board and subset comparisons", flush=True)


if __name__ == "__main__":
    main()
