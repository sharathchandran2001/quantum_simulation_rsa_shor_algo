# ========================== 
# 🔓 Quantum RSA Demo using Shor's Algorithm + Visualization
# ==========================

# Install required libraries quietly
!pip install pennylane matplotlib --quiet

# --- Imports ---
import pennylane as qml          # Quantum computing library (hybrid quantum-classical workflows)
import numpy as np              # Numerical computations
from fractions import Fraction  # For rational approximations of phase estimates
from math import gcd            # Greatest common divisor (used for factorization step)
import time                     # Benchmark timing
import random                   # Random number generation (pick random base 'a')
import matplotlib.pyplot as plt # Visualization

# -------------------------------------
# Utility: Extract non-trivial factors from period 'r'
# -------------------------------------
def get_factors(a, N, r):
    """
    Given:
        a : Randomly chosen integer (coprime to N)
        N : Composite number to factor
        r : Estimated period from quantum phase estimation

    Returns:
        (f1, f2) if valid non-trivial factors are found, else None.
    """

    # If r is odd, Shor’s algorithm cannot continue reliably
    if r % 2 != 0:
        print("⚠️ Period r is odd. Skipping.")
        return None

    # Compute (a^(r/2) ± 1)
    plus = pow(a, r // 2) + 1
    minus = pow(a, r // 2) - 1

    # Compute GCD with N to try extracting non-trivial factors
    f1 = gcd(plus, N)
    f2 = gcd(minus, N)

    print(f"Trying GCD({plus},{N}) = {f1}, GCD({minus},{N}) = {f2}")

    # Discard trivial factors (1 or N itself)
    if f1 in [1, N] or f2 in [1, N]:
        return None

    return f1, f2


# -------------------------------------
# Simulate Shor's Algorithm
# -------------------------------------
def run_shor_sim(N, a=None, n_count=12):
    """
    Run a classical simulation of Shor's algorithm using PennyLane.

    Args:
        N (int): Composite number to factor.
        a (int, optional): Random base integer. If None, a random valid base is chosen.
        n_count (int): Number of qubits for phase estimation (default = 12).

    Returns:
        dict: Results including 'a', 'bitstring', 'phase', 'r', 'factors', and timing info.
    """

    # Total qubits = counting register + workspace (extra)
    total_wires = n_count + 6  
    dev = qml.device('default.qubit', wires=total_wires, shots=1)

    # Pick a random base 'a' if not provided, must be coprime to N
    if a is None:
        while True:
            a = random.randint(2, N - 1)
            if gcd(a, N) == 1:
                break

    # Define controlled modular exponentiation (placeholder simulation)
    def controlled_modular_exponentiation():
        for i in range(n_count):
            exponent = 2 ** i
            angle = (2 * np.pi * pow(a, exponent, N)) / N
            qml.ctrl(qml.RZ, control=i)(angle, wires=n_count)

    # Quantum node: Phase estimation + modular exponentiation
    @qml.qnode(dev)
    def shor_circuit():
        # Apply Hadamards on counting register
        for i in range(n_count):
            qml.Hadamard(wires=i)

        # Controlled modular exponentiation (simulated)
        controlled_modular_exponentiation()

        # Swap qubits to reverse order for QFT
        for i in range(n_count // 2):
            qml.SWAP(wires=[i, n_count - i - 1])

        # Approximate Inverse Quantum Fourier Transform (IQFT)
        for j in range(n_count):
            qml.Hadamard(wires=j)
            for k in range(j + 1, n_count):
                angle = -np.pi / (2 ** (k - j))
                qml.ctrl(qml.RZ, control=k)(angle, wires=j)

        # Measure counting register as bitstring
        return qml.sample(wires=range(n_count))

    # Run circuit and process results
    start = time.time()
    measurement = shor_circuit()

    # Convert measured bits → integer y
    bitstring = ''.join(str(b) for b in measurement)
    y = int(bitstring, 2)

    # Compute phase = y / 2^n_count
    phase = y / (2 ** n_count)

    # Find rational approximation of phase → denominator ~ r
    frac = Fraction(phase).limit_denominator(N)
    r = frac.denominator

    # Try factor extraction
    factors = get_factors(a, N, r)
    elapsed = time.time() - start

    return {
        "a": a,
        "y": y,
        "phase": phase,
        "r": r,
        "factors": factors,
        "elapsed_time": elapsed,
        "bitstring": bitstring
    }


# -------------------------------------
# Run Attempts to Factor N
# -------------------------------------
N = 181  # Example semi-prime
max_attempts = 50000
attempt_times = []
success_result = None
start_total = time.time()

# Attempt multiple times until success or limit reached
for attempt in range(1, max_attempts + 1):
    print(f"\n🔁 Attempt {attempt} to factor N = {N}")
    start_iter = time.time()

    results = run_shor_sim(N)
    iter_time = time.time() - start_iter
    attempt_times.append(iter_time)

    # Debug info per attempt
    print("Randomly selected a =", results["a"])
    print("Measurement bitstring =", results["bitstring"])
    print("Measured integer y =", results["y"])
    print("Estimated phase = {:.6f}".format(results["phase"]))
    print("Estimated period r =", results["r"])
    print("Elapsed time = {:.4f} seconds".format(results["elapsed_time"]))

    # If valid factors found → break loop
    if results["factors"]:
        success_result = results
        break

end_total = time.time()
total_duration = end_total - start_total
average_iter_time = np.mean(attempt_times)


# -------------------------------------
# Summary Output
# -------------------------------------
print("\n===============================")
if success_result:
    print(f"✅ SUCCESS after {attempt} attempts")
    print(f"🔐 N = {N} factored into: {success_result['factors']}")
    print(f"🕒 Total time to find solution: {total_duration:.4f} seconds")
    print(f"⏱️ Average time per attempt: {average_iter_time:.4f} seconds")
    print(f"🧠 Total qubits used: {12 + 6} (Counting: 12, Extra: 6)")
else:
    print("❌ Failed to factor the number after max attempts.")
    print(f"⏱️ Total time: {total_duration:.4f} seconds")
    print(f"⏱️ Average attempt time: {average_iter_time:.4f} seconds")
print("===============================")


# -------------------------------------
# Visualization
# -------------------------------------

# Plot 1: Time per Attempt
plt.figure(figsize=(10, 4))
plt.plot(range(1, len(attempt_times) + 1), attempt_times, marker='o')
plt.title("⏱️ Time Taken per Attempt")
plt.xlabel("Attempt #")
plt.ylabel("Time (seconds)")
plt.grid(True)
plt.show()

# Plot 2: Factorization Result
if success_result:
    factors = success_result['factors']
    plt.figure(figsize=(5, 4))
    plt.bar(["Factor 1", "Factor 2"], [factors[0], factors[1]], color='skyblue')
    plt.title(f"🔐 Factors of N = {N}")
    plt.ylabel("Value")
    plt.grid(axis='y')
    plt.show()

# Plot 3: Phase vs Rational Approximation
if success_result:
    phase = success_result['phase']
    approx_frac = Fraction(phase).limit_denominator(N)

    plt.figure(figsize=(6, 4))
    plt.axvline(phase, color='red', linestyle='--', label=f"Estimated phase = {phase:.5f}")
    plt.axvline(float(approx_frac), color='green', linestyle='--', label=f"Rational approx = {float(approx_frac):.5f}")
    plt.title("📉 Phase Estimation vs Rational Approximation")
    plt.xlabel("Value")
    plt.legend()
    plt.grid(True)
    plt.show()
