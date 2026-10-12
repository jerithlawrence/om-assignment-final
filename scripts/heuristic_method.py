"""Random-start nearest neighbour followed by best-improvement 2-opt."""

import numpy as np


def tour_length(route, distance):
    """Include the last-to-first edge; route itself contains no repeat."""
    route = np.asarray(route, dtype=int)
    return int(distance[route, np.roll(route, -1)].sum())


def local_search(distance, seed):
    """Return a feasible 2-opt local optimum, initial cost and cost history.

    Only the start is random. Nearest-neighbour ties use smallest index;
    equal 2-opt improvements use row-major order. No iteration/time cap.
    """
    n = len(distance)
    rng = np.random.default_rng(seed)
    route = [int(rng.integers(n))]
    unused = set(range(n)) - set(route)
    while unused:
        node = min(unused, key=lambda j: (distance[route[-1], j], j))
        route.append(node)
        unused.remove(node)
    route = np.array(route)
    history = [tour_length(route, distance)]
    # Nonadjacent edge pairs only; first and last edges are adjacent too.
    i, j = np.triu_indices(n, k=2)
    valid = ~((i == 0) & (j == n - 1))
    i, j = i[valid], j[valid]
    while len(i):
        successor = np.roll(route, -1)
        delta = (distance[route[i], route[j]]
                 + distance[successor[i], successor[j]]
                 - distance[route[i], successor[i]]
                 - distance[route[j], successor[j]])
        move = int(np.argmin(delta))
        if delta[move] >= 0:
            break
        left, right = int(i[move]) + 1, int(j[move]) + 1
        route[left:right] = route[left:right][::-1]
        history.append(history[-1] + int(delta[move]))
    assert tour_length(route, distance) == history[-1]
    return route, history[0], history
