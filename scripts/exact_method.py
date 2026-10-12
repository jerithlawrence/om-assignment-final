"""Held–Karp dynamic programming for small symmetric TSP instances."""

import numpy as np


def held_karp(distance):
    """Return a globally optimal permutation and its closed-tour cost.

    State (mask, j) is a shortest path from node 0 through exactly mask,
    ending at j + 1. Bits represent nodes 1 through n - 1.
    Time O(n^2 2^n); space O(n 2^n). Limit n to protect memory/runtime.
    """
    n = len(distance)
    if not 3 <= n <= 20:
        raise ValueError("Held–Karp supports 3 to 20 nodes in this project")
    m = n - 1
    states = 1 << m
    infinity = np.iinfo(np.int64).max // 4
    cost = np.full((states, m), infinity, dtype=np.int64)
    parent = np.full((states, m), -1, dtype=np.int8)
    for j in range(m):
        cost[1 << j, j] = distance[0, j + 1]
    for mask in range(1, states):
        remaining = mask
        while remaining:
            bit = remaining & -remaining
            j = bit.bit_length() - 1
            previous = mask ^ bit
            if previous:
                candidates = previous
                best, predecessor = infinity, -1
                while candidates:
                    kbit = candidates & -candidates
                    k = kbit.bit_length() - 1
                    value = cost[previous, k] + distance[k + 1, j + 1]
                    if value < best:
                        best, predecessor = value, k
                    candidates ^= kbit
                cost[mask, j] = best
                parent[mask, j] = predecessor
            remaining ^= bit
    last_costs = cost[-1] + distance[1:, 0]
    j = int(np.argmin(last_costs))
    optimum = int(last_costs[j])
    mask, reverse_path = states - 1, []
    while mask:
        reverse_path.append(j + 1)
        predecessor = int(parent[mask, j])
        mask ^= 1 << j
        j = predecessor
    return np.array([0] + reverse_path[::-1]), optimum
