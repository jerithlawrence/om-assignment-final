"""Exact TSP model with SCIP branch-and-bound and subtour constraints.

Connectivity callbacks follow the PySCIPOpt constraint-handler interface:
https://github.com/scipopt/PySCIPOpt/blob/master/tests/test_tsp.py
"""

from time import perf_counter

import numpy as np
from pyscipopt import Conshdlr, Model, SCIP_RESULT, quicksum

from heuristic_method import local_search, tour_length


class Connectivity(Conshdlr):
    """Reject disconnected cycles and add valid subtour inequalities."""

    def __init__(self, n, edges):
        self.n, self.edges, self.cuts = n, edges, 0

    def components(self, solution=None):
        neighbours = [[] for _ in range(self.n)]
        for (a, b), variable in self.edges.items():
            if self.model.getSolVal(solution, variable) > 1e-6:
                neighbours[a].append(b)
                neighbours[b].append(a)
        remaining, groups = set(range(self.n)), []
        while remaining:
            stack = [remaining.pop()]
            group = set(stack)
            while stack:
                for b in neighbours[stack.pop()]:
                    if b in remaining:
                        remaining.remove(b)
                        group.add(b)
                        stack.append(b)
            groups.append(sorted(group))
        return groups

    def conscheck(self, constraints, solution, *args, **kwargs):
        connected = len(self.components(solution)) == 1
        return {"result": (SCIP_RESULT.FEASIBLE if connected
                           else SCIP_RESULT.INFEASIBLE)}

    def consenfolp(self, constraints, *args, **kwargs):
        groups = self.components()
        if len(groups) == 1:
            return {"result": SCIP_RESULT.FEASIBLE}
        for group in groups:
            internal = (self.edges[a, b] for k, a in enumerate(group)
                        for b in group[k + 1:])
            self.model.addCons(quicksum(internal) <= len(group) - 1)
            self.cuts += 1
        return {"result": SCIP_RESULT.CONSADDED}

    def conslock(self, *args):
        # Degree equalities already lock every variable in both directions.
        pass


def solve_ilp(distance, time_limit=300):
    """Return a valid tour and solver evidence; a time limit is not proof.

    All n(n-1)/2 edges are included. Seed-0 NN + 2-opt provides a feasible
    warm start, included in total runtime. No published tour or value is
    supplied to the optimizer. Disconnected cycle covers are never returned.
    """
    start = perf_counter()
    n = len(distance)
    model = Model("pcb_tsp")
    model.hideOutput()
    model.setIntParam("parallel/maxnthreads", 1)
    model.setIntParam("randomization/randomseedshift", 0)
    model.setBoolParam("misc/allowstrongdualreds", False)
    model.setRealParam("limits/time", float(time_limit))
    model.setRealParam("limits/gap", 0.0)
    model.setRealParam("numerics/feastol", 1e-6)
    edges = {(a, b): model.addVar(vtype="B", obj=int(distance[a, b]))
             for a in range(n) for b in range(a + 1, n)}
    incident = [[] for _ in range(n)]
    for (a, b), variable in edges.items():
        incident[a].append(variable)
        incident[b].append(variable)
    for variables in incident:
        model.addCons(quicksum(variables) == 2)
    handler = Connectivity(n, edges)
    model.includeConshdlr(handler, "connectivity", "one complete tour",
                         chckpriority=-10, needscons=False)
    initial, _, _ = local_search(distance, seed=0)
    solution = model.createSol()
    for a, b in zip(initial, np.roll(initial, -1)):
        model.setSolVal(solution, edges[min(a, b), max(a, b)], 1)
    model.addSol(solution)
    model.optimize()
    neighbours = [[] for _ in range(n)]
    for (a, b), variable in edges.items():
        if model.getVal(variable) > 0.5:
            neighbours[a].append(b)
            neighbours[b].append(a)
    if any(len(v) != 2 for v in neighbours):
        raise ValueError("SCIP did not return degree-two edges")
    route, previous, current = [], -1, 0
    while current not in route:
        route.append(current)
        following = next(v for v in neighbours[current] if v != previous)
        previous, current = current, following
    if current != 0 or sorted(route) != list(range(n)):
        raise ValueError("SCIP returned a disconnected or invalid cycle")
    cost = tour_length(route, distance)
    if abs(cost - model.getObjVal()) > 1e-5:
        raise ValueError("SCIP objective differs from integer tour cost")
    evidence = dict(
        distance=cost, initial_distance=tour_length(initial, distance),
        runtime_seconds=perf_counter() - start,
        solver_seconds=model.getSolvingTime(),
        status=str(model.getStatus()), lower_bound=model.getDualbound(),
        solver_gap=model.getGap(), branch_nodes=model.getNNodes(),
        subtour_constraints=handler.cuts, time_limit_seconds=time_limit,
        variables=len(edges), scip_version="{}.{}.{}".format(
            model.getMajorVersion(), model.getMinorVersion(),
            model.getTechVersion()))
    return np.array(route), evidence
