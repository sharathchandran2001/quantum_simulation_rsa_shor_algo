
############################################################################  Quantum simulated Shor (N=15)
############################################################################
############################################################################
############################################################################
# Install necessary packages (if not already installed)
# !pip install pennylane matplotlib


# in RSA-2048 - The encryption is based on a 2048-bit integer
# p and q are each ~1024 bits long (very large)
# N = 25195908475657893494027183240048398571429282126204... (617 decimal digits)
# Exponential time classically & Takes millions of years to break RSA


# Imports
import pennylane as qml
import numpy as np
import matplotlib.pyplot as plt
from fractions import Fraction
from math import gcd
import time
import random

# ----- Utility Functions -----

def get_factors(a, N, r):
    """Classically extract factors from period r."""
    if r % 2 != 0:
        return None
    plus = pow(a, r // 2) + 1
    minus = pow(a, r // 2) - 1
    f1 = gcd(plus, N)
    f2 = gcd(minus, N)
    if f1 == 1 or f2 == 1 or f1 == N or f2 == N:
        return None
    return f1, f2

def run_shor_sim(N, a=None, n_count=8):
    """Simulate Shor's algorithm for small N using PennyLane."""
    total_wires = n_count + 6  # 8 counting qubits + 6 target qubits (more space for N=55)
    dev = qml.device('default.qubit', wires=total_wires, shots=1)

    # Choose a random a coprime with N if not provided
    if a is None:
        while True:
            a = random.randint(2, N-1)
            if gcd(a, N) == 1:
                break

    # Define modular exponentiation placeholder
    def controlled_modular_exponentiation():
        for i in range(n_count):
            exponent = 2 ** i
            angle = (2 * np.pi * pow(a, exponent, N)) / N
            qml.ctrl(qml.RZ, control=i)(angle, wires=n_count)

    @qml.qnode(dev)
    def shor_circuit():
        # 1. Apply Hadamards to counting qubits
        for i in range(n_count):
            qml.Hadamard(wires=i)

        # 2. Simulate modular exponentiation
        controlled_modular_exponentiation()

        # 3. Inverse QFT
        for i in range(n_count // 2):
            qml.SWAP(wires=[i, n_count - i - 1])
        for j in range(n_count):
            qml.Hadamard(wires=j)
            for k in range(j + 1, n_count):
                angle = -np.pi / (2 ** (k - j))
                qml.ctrl(qml.RZ, control=k)(angle, wires=j)

        return qml.sample(wires=range(n_count))

    # ---- Run Simulation ----
    start = time.time()
    measurement = shor_circuit()
    bitstring = ''.join(str(b) for b in measurement)
    y = int(bitstring, 2)
    phase = y / (2 ** n_count)

    # Estimate period using continued fractions
    frac = Fraction(phase).limit_denominator(N)
    r = frac.denominator
    factors = get_factors(a, N, r)
    elapsed = time.time() - start

    return factors, elapsed, a, r

# ------------------------
# Attempt to factor N = 55
# ------------------------

N = 55
attempts = 5000

for attempt in range(attempts):
    print(f"\n--- Attempt {attempt+1} ---")
    factors, elapsed, a, r = run_shor_sim(N)
    print(f"Randomly selected a = {a}")
    print(f"Estimated period r = {r}")
    if factors:
        print(f"✅ Quantum simulated Shor (N={N}): Factors = {factors}, Time = {elapsed:.4f}s (Attempt {attempt+1})")
        break
    else:
        print(f"❌ No valid factors found in attempt {attempt+1} (a={a}, r={r})")

else:
    print(f"\n❌ Quantum simulated Shor (N={N}): No factors found after {attempts} attempts.")
