import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import numpy as np

β = 0.0065
λ = 0.08
Λ = 0.001
t_span = (0,60)

n0 = 1.0
C0 = β/(λ*Λ)*n0
y0 = [n0, C0]


def reactivity(t) -> float:
    ramp_rate = 0.0001

    if t < 5.0:
        return 0.0
    elif t < 40.0:
        return ramp_rate * (t-5.0)
    elif t < 50.0:
        k = 1.001
        return (k - 1) / k
    else:
        return -0.05

def prke(t, y):
    n = y[0]
    C = y[1]

    rho = reactivity(t)

    dn_dt = ((rho-β)/Λ)*n+λ*C
    dC_dt = (β/Λ)*n-λ*C

    return[dn_dt, dC_dt]

solution = solve_ivp(
    fun=prke,
    t_span=t_span,
    y0=y0,
    method='RK45',
    t_eval=np.linspace(0, 60, 1000)
)

time = solution.t
power = solution.y[0]
precursors = solution.y[1]

rho_history = [reactivity(t) for t in time]
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(9, 8), sharex=True)

ax1.plot(time, rho_history, color='tab:red', lw=2)
ax1.set_ylabel(r"Reactivity $\rho(t)$")
ax1.grid(True, alpha=0.3)
ax1.set_title("Point Reactor Kinetics Simulation", fontsize=14, fontweight='bold')

ax2.plot(time, power, color='tab:blue', lw=2, label="Relative Power $n(t)$")
ax2.set_ylabel("Power (Linear)")
ax2.grid(True, alpha=0.3)
ax2.legend(loc="upper left")

ax3.semilogy(time, power, color='tab:blue', lw=2, label="Power $n(t)$")
ax3.semilogy(time, precursors, color='tab:orange', lw=2, linestyle='--', label="Precursors $C(t)$")
ax3.set_ylabel("Log Scale")
ax3.set_xlabel("Time (seconds)")
ax3.grid(True, which="both", alpha=0.3)
ax3.legend(loc="upper left")

plt.tight_layout()
plt.show()