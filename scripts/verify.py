"""Independent correctness checks; run before the experiment pipeline."""

from itertools import permutations

import numpy as np

from exact_method import held_karp
from heuristic_method import local_search, tour_length
from main import ROOT, distance_matrix, load_dataset, validate_tour


def main():
    _, xy = load_dataset(ROOT / "dataset" / "pcb442.tsp")
    assert xy.shape == (442, 2)
    distance = distance_matrix(xy)
    assert np.array_equal(distance, distance.T)
    assert np.all(np.diag(distance) == 0)
    # Half-up rounding must differ from Python's banker's rounding at 2.5.
    assert distance_matrix(np.array([[0, 0], [2.5, 0]]))[0, 1] == 3
    rng = np.random.default_rng(123)
    for n in (4, 6, 8):
        d = distance_matrix(rng.uniform(0, 100, (n, 2)))
        brute = min(tour_length((0,) + p, d)
                    for p in permutations(range(1, n)))
        route, optimum = held_karp(d)
        validate_tour(route, d, optimum)
        assert optimum == brute
        for seed in range(5):
            route, initial, history = local_search(d, seed)
            validate_tour(route, d, history[-1])
            assert initial >= history[-1] >= optimum
            assert all(a > b for a, b in zip(history, history[1:]))
            # Exhaustively verify termination with no improving 2-opt move.
            for i in range(n):
                for j in range(i + 2, n):
                    trial = route.copy()
                    trial[i + 1:j + 1] = trial[i + 1:j + 1][::-1]
                    assert tour_length(trial, d) >= history[-1]
    try:
        validate_tour([0, 1, 1, 3], np.zeros((4, 4)), 0)
    except ValueError:
        pass
    else:
        raise AssertionError("Duplicate visit was not rejected")
    print("PASS: rounding, closure, brute-force agreement, feasibility, 2-opt")


if __name__ == "__main__":
    main()
