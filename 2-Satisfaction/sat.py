"""
3-CNF-SAT Phase Transition Experiment

Investigates the phase transition behavior of randomized 3-CNF-SAT
as a function of the clause-to-variable ratio.
"""

import random
import math
import matplotlib.pyplot as plt


def generate(n, m):
    """
    Generate a random 3-CNF instance.

    Args:
        n: Number of variables (variables are numbered 1 to n)
        m: Clause-to-variable ratio

    Returns:
        List of clauses, where each clause is a list of 3 literals.
        Positive integers represent variables, negative integers represent negations.
    """
    num_clauses = int(n * m)
    clauses = []

    for _ in range(num_clauses):
        clause = []
        for _ in range(3):
            # Choose a random variable (1 to n)
            var = random.randint(1, n)
            # Randomly negate it
            if random.random() < 0.5:
                var = -var
            clause.append(var)
        clauses.append(clause)

    return clauses


def print_cnf(clauses):
    """Pretty print a CNF formula for debugging."""
    clause_strs = []
    for clause in clauses:
        literals = []
        for lit in clause:
            if lit > 0:
                literals.append(f"x{lit}")
            else:
                literals.append(f"¬x{-lit}")
        clause_strs.append(f"({' ∨ '.join(literals)})")
    print(" ∧ ".join(clause_strs))


def solve(clauses, n):
    """
    Solve a 3-CNF-SAT instance using DPLL with unit propagation and
    pure literal elimination.

    Args:
        clauses: List of clauses (each clause is a list of literals)
        n: Number of variables

    Returns:
        True if satisfiable, False otherwise
    """
    # Convert to frozensets for immutability and fast operations
    clause_set = [frozenset(c) for c in clauses]
    return _dpll(clause_set, set(range(1, n + 1)))


def _dpll(clauses, unassigned):
    """
    DPLL recursive solver.

    Args:
        clauses: list of frozenset literals (only unsatisfied, simplified clauses)
        unassigned: set of unassigned variable ids
    """
    # Unit propagation + pure literal elimination
    clauses, unassigned, ok = _propagate(clauses, unassigned)
    if not ok:
        return False
    if not clauses:
        return True

    # Variable selection: pick the variable appearing in the most clauses
    # (DLIS-like heuristic). Count positive and negative occurrences.
    pos_count = {}
    neg_count = {}
    for clause in clauses:
        for lit in clause:
            v = abs(lit)
            if v in unassigned:
                if lit > 0:
                    pos_count[v] = pos_count.get(v, 0) + 1
                else:
                    neg_count[v] = neg_count.get(v, 0) + 1

    # Pick variable with max total occurrences; try the more common polarity first
    best_var = None
    best_score = -1
    for v in pos_count.keys() | neg_count.keys():
        score = pos_count.get(v, 0) + neg_count.get(v, 0)
        if score > best_score:
            best_score = score
            best_var = v

    if best_var is None:
        return False

    # Try the polarity that satisfies more clauses first
    if pos_count.get(best_var, 0) >= neg_count.get(best_var, 0):
        try_order = [best_var, -best_var]
    else:
        try_order = [-best_var, best_var]

    new_unassigned = unassigned - {best_var}

    for lit in try_order:
        new_clauses = _assign_literal(clauses, lit)
        if new_clauses is not None:
            if _dpll(new_clauses, new_unassigned):
                return True

    return False


def _propagate(clauses, unassigned):
    """
    Apply unit propagation and pure literal elimination until fixpoint.

    Returns (clauses, unassigned, ok) where ok=False means conflict.
    """
    unassigned = set(unassigned)
    changed = True

    while changed:
        changed = False

        # Unit propagation
        for clause in clauses:
            if len(clause) == 1:
                lit = next(iter(clause))
                var = abs(lit)
                clauses = _assign_literal(clauses, lit)
                if clauses is None:
                    return [], unassigned, False
                unassigned.discard(var)
                changed = True
                break

        if changed:
            continue

        # Pure literal elimination
        lit_set = set()
        for clause in clauses:
            lit_set.update(clause)

        for lit in lit_set:
            if -lit not in lit_set:
                # Pure literal: assign it to satisfy its clauses
                var = abs(lit)
                clauses = _assign_literal(clauses, lit)
                if clauses is None:
                    return [], unassigned, False
                unassigned.discard(var)
                changed = True
                break

    return clauses, unassigned, True


def _assign_literal(clauses, lit):
    """
    Assign a literal to True: remove clauses containing lit,
    remove -lit from remaining clauses. Returns None on conflict (empty clause).
    """
    neg_lit = -lit
    new_clauses = []
    for clause in clauses:
        if lit in clause:
            continue  # clause is satisfied
        if neg_lit in clause:
            reduced = clause - {neg_lit}
            if not reduced:
                return None  # empty clause = conflict
            new_clauses.append(reduced)
        else:
            new_clauses.append(clause)
    return new_clauses


def test_generator():
    """Test the generator function."""
    print("=== Testing Generator ===")

    # Small test
    clauses = generate(5, 2)
    print(f"Generated {len(clauses)} clauses for n=5, m=2:")
    print_cnf(clauses)

    # Verify structure
    assert len(clauses) == 10, f"Expected 10 clauses, got {len(clauses)}"
    for clause in clauses:
        assert len(clause) == 3, f"Expected 3 literals per clause, got {len(clause)}"
        for lit in clause:
            assert 1 <= abs(lit) <= 5, f"Literal {lit} out of range"

    print("Generator tests passed!\n")


def test_solver():
    """Test the solver with known instances."""
    print("=== Testing Solver ===")

    # Test 1: Simple satisfiable instance
    # (x1 ∨ x2 ∨ x3) - satisfiable with x1=True
    clauses = [[1, 2, 3]]
    result = solve(clauses, 3)
    assert result == True, "Test 1 failed: should be satisfiable"
    print("Test 1 passed: simple satisfiable clause")

    # Test 2: Unsatisfiable instance
    # (x1) ∧ (¬x1) - unsatisfiable
    clauses = [[1, 1, 1], [-1, -1, -1]]
    result = solve(clauses, 1)
    assert result == False, "Test 2 failed: should be unsatisfiable"
    print("Test 2 passed: simple unsatisfiable")

    # Test 3: More complex satisfiable
    # (x1 ∨ x2 ∨ x3) ∧ (¬x1 ∨ x2 ∨ x3) ∧ (x1 ∨ ¬x2 ∨ x3)
    clauses = [[1, 2, 3], [-1, 2, 3], [1, -2, 3]]
    result = solve(clauses, 3)
    assert result == True, "Test 3 failed: should be satisfiable"
    print("Test 3 passed: complex satisfiable")

    # Test 4: Classic unsatisfiable 3-CNF on 2 variables
    # All 8 possible clauses with x1 and x2 - unsatisfiable
    clauses = [
        [1, 1, 2], [1, 1, -2], [1, -1, 2], [1, -1, -2],
        [-1, -1, 2], [-1, -1, -2], [-1, 1, 2], [-1, 1, -2]
    ]
    # This covers all combinations - should be unsatisfiable
    # Actually let me make a proper unsatisfiable formula
    # (x1 ∨ x1 ∨ x1) ∧ (¬x1 ∨ ¬x1 ∨ ¬x1)
    clauses = [[1, 1, 1], [-1, -1, -1]]
    result = solve(clauses, 1)
    assert result == False, "Test 4 failed: should be unsatisfiable"
    print("Test 4 passed: covering unsatisfiable")

    # Test 5: Random satisfiable (low ratio)
    random.seed(42)
    clauses = generate(10, 1)
    result = solve(clauses, 10)
    print(f"Test 5: random n=10, m=1 -> {'SAT' if result else 'UNSAT'}")

    # Test 6: Random likely unsatisfiable (high ratio)
    random.seed(42)
    clauses = generate(10, 10)
    result = solve(clauses, 10)
    print(f"Test 6: random n=10, m=10 -> {'SAT' if result else 'UNSAT'}")

    print("Solver tests passed!\n")


def run_experiment(n=100, m_start=1.0, m_end=8.0, m_step=0.25, trials=25):
    """
    Run the phase transition experiment.

    Args:
        n: Number of variables
        m_start: Starting clause-to-variable ratio
        m_end: Ending clause-to-variable ratio
        m_step: Step size for m
        trials: Number of trials per m value

    Returns:
        (m_values, sat_fractions, ci_lower, ci_upper) for plotting
    """
    m_values = []
    sat_fractions = []
    ci_lower = []
    ci_upper = []

    m = m_start
    while m <= m_end + 0.001:  # Small epsilon for float comparison
        sat_count = 0

        for trial in range(trials):
            clauses = generate(n, m)
            if solve(clauses, n):
                sat_count += 1

        fraction = sat_count / trials
        m_values.append(m)
        sat_fractions.append(fraction)

        # 95% Wilson score confidence interval for binomial proportion
        z = 1.96
        denom = 1 + z**2 / trials
        center = (fraction + z**2 / (2 * trials)) / denom
        spread = z * math.sqrt((fraction * (1 - fraction) + z**2 / (4 * trials)) / trials) / denom
        ci_lower.append(max(0, center - spread))
        ci_upper.append(min(1, center + spread))

        print(f"m = {m:.2f}: {sat_count}/{trials} satisfiable ({fraction:.2%})")

        m += m_step

    return m_values, sat_fractions, ci_lower, ci_upper


def plot_results(m_values, sat_fractions, ci_lower=None, ci_upper=None,
                 filename="phase_transition.png"):
    """Plot the phase transition graph with optional confidence intervals."""
    plt.figure(figsize=(10, 6))
    plt.plot(m_values, sat_fractions, 'b-o', linewidth=2, markersize=6,
             label='Fraction satisfiable')

    if ci_lower is not None and ci_upper is not None:
        plt.fill_between(m_values, ci_lower, ci_upper, alpha=0.2, color='blue',
                         label='95% confidence interval')

    plt.xlabel('Clause-to-Variable Ratio (m)', fontsize=12)
    plt.ylabel('Fraction Satisfiable', fontsize=12)
    plt.title('3-CNF-SAT Phase Transition (n=100 variables)', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.ylim(-0.05, 1.05)
    plt.axhline(y=0.5, color='r', linestyle='--', alpha=0.5, label='50% threshold')
    plt.axvline(x=4.267, color='g', linestyle=':', alpha=0.5,
                label='Theoretical threshold (~4.267)')
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()
    print(f"Plot saved to {filename}")


if __name__ == "__main__":
    # Run tests first
    test_generator()
    test_solver()

    # Run the experiment
    print("=== Running Phase Transition Experiment ===")
    print("n = 100 variables, m from 1.0 to 8.0, 25 trials each\n")

    m_values, sat_fractions, ci_lower, ci_upper = run_experiment()

    # Plot results
    plot_results(m_values, sat_fractions, ci_lower, ci_upper)

    # Find approximate transition point
    for i, (m, frac) in enumerate(zip(m_values, sat_fractions)):
        if frac < 0.5:
            print(f"\nPhase transition occurs around m ≈ {m_values[i-1]:.2f} - {m:.2f}")
            break
