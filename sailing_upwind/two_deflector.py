"""Two-deflector model: sail and centreboard modelled symmetrically.

This extends the one-deflector model by removing the infinite-lateral-resistance
assumption.

The sail is kept as a momentum-deflector (same as the base model).  The
centreboard is modelled as a *low-drag lifting surface* whose side-force grows
linearly with leeway angle alpha at small angles (thin-flat-plate theory,
C_L = 2*pi*sin(alpha) ≈ 2*pi*alpha) and whose induced drag adds a small
forward-drag penalty.  This is more realistic than applying the deflector
equation to the centreboard, which would require ~12° leeway before any
side-force appeared (far too much).

Reference frames
----------------
x' : along the boat's heading (positive = forward)
y' : across the boat (positive = to leeward)

Sail forces  (full 2-D decomposition of the deflector equation)
---------------------------------------------------------------
Incoming wind momentum flux in boat frame arrives at angle theta:

    F_sail_x = rho_a * a_s * v_s^2 * |sin(theta)| * (D_s - cos(theta))
    F_sail_y = rho_a * a_s * v_s^2 * sin^2(theta)          [leeward]

Centreboard forces  (lifting-surface model)
-------------------------------------------
The centreboard moves sideways through the water at speed v*sin(alpha).
Using thin-plate lift: C_L = 2*pi*sin(alpha), C_D = C_L^2 / (pi*AR)
where AR is the aspect ratio of the centreboard (span^2 / area).

    F_cb_y = 0.5 * rho_w * A_c * C_L(alpha) * v^2          [windward]
    F_cb_x = -0.5 * rho_w * A_c * C_D(alpha) * v^2         [drag]

Hull drag (unchanged)
---------------------
    F_hull = -(1 - D_h) * rho_w * A_h * v^2

Equilibrium
-----------
Forward:   F_sail_x + F_cb_x = F_hull
Lateral:   F_sail_y = F_cb_y

Optimisation
------------
Maximise  u_true = v * cos(theta + alpha)  over theta.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from scipy.optimize import fsolve


@dataclass
class TwoDeflectorParams:
    """All parameters needed by the two-deflector model."""
    v_s: float          # true wind speed (m/s)
    a_s: float          # sail area (m^2)
    rho_a: float        # air density (kg/m^3)
    D_s: float          # sail drag coefficient
    A_c: float          # centreboard planform area (m^2)
    AR_c: float = 6.0   # centreboard aspect ratio (span^2/area); ~6 for a dinghy
    D_h: float = 0.9    # hull drag coefficient
    rho_w: float = 1000.0
    A_h: float = 0.0343  # hull frontal area (m^2)


def _centreboard_forces(alpha: float, v: float, p: TwoDeflectorParams) -> tuple[float, float]:
    """Side-force (windward) and drag of the centreboard.

    Uses thin-flat-plate lift theory: C_L = 2*pi*sin(alpha), with
    induced drag C_Di = C_L^2 / (pi * AR).

    Returns (F_y_windward, F_x_drag) — F_y is positive to windward,
    F_x_drag is positive (magnitude), applied as -F_x_drag forward.
    """
    CL = 2.0 * math.pi * math.sin(alpha)
    CD = CL**2 / (math.pi * p.AR_c)
    q = 0.5 * p.rho_w * p.A_c * v**2
    return q * CL, q * CD  # (side-force, drag)


def _equilibrium_residuals(
    x: tuple[float, float],
    theta: float,
    p: TwoDeflectorParams,
) -> list[float]:
    """Residuals of the two equilibrium equations at (v, alpha)."""
    v, alpha = x
    if v <= 0.0 or alpha < 0.0:
        return [1e6, 1e6]

    sin_t = math.sin(theta)
    cos_t = math.cos(theta)

    # Sail forces
    F_sail_x = p.rho_a * p.a_s * p.v_s**2 * abs(sin_t) * (p.D_s - cos_t)
    F_sail_y = p.rho_a * p.a_s * p.v_s**2 * sin_t**2

    # Centreboard forces
    F_cb_y, F_cb_drag = _centreboard_forces(alpha, v, p)

    # Hull drag
    F_hull = (1.0 - p.D_h) * p.rho_w * p.A_h * v**2

    fwd = F_sail_x - F_cb_drag - F_hull
    lat = F_sail_y - F_cb_y
    return [fwd, lat]


def solve_equilibrium(
    theta: float,
    p: TwoDeflectorParams,
    v0: float = 2.0,
    alpha0: float = 0.05,
) -> Optional[tuple[float, float]]:
    """Return (v, alpha) at equilibrium for heading *theta*, or None."""
    if p.D_s - math.cos(theta) <= 0:
        return None

    for v_try in ([v0] + [0.5, 1.0, 2.0, 3.0, 4.0]):
        for a_try in ([alpha0] + [0.01, 0.03, 0.05, 0.10]):
            sol, info, ier, _ = fsolve(
                _equilibrium_residuals,
                x0=[v_try, a_try],
                args=(theta, p),
                full_output=True,
            )
            v, alpha = sol
            res = _equilibrium_residuals([v, alpha], theta, p)
            if (ier == 1 and v > 0.0 and 0.0 <= alpha <= math.radians(20)
                    and max(abs(r) for r in res) < 1e-4):
                return float(v), float(alpha)
    return None


def upwind_speed(theta: float, p: TwoDeflectorParams) -> float:
    """True upwind component v*cos(theta+alpha) at heading *theta* (m/s).

    Examples
    --------
    >>> import math
    >>> p = TwoDeflectorParams(
    ...     v_s=4.0, a_s=5.1, rho_a=1.225, D_s=0.895,
    ...     A_c=0.125, AR_c=6.0, D_h=0.9, rho_w=1000.0, A_h=0.0343,
    ... )
    >>> u = upwind_speed(math.radians(57), p)
    >>> u > 0
    True
    """
    sol = solve_equilibrium(theta, p)
    if sol is None:
        return 0.0
    v, alpha = sol
    return v * math.cos(theta + alpha)


def optimal_angle(
    p: TwoDeflectorParams,
    n_grid: int = 500,
) -> tuple[float, float, float]:
    """Find heading angle maximising true upwind speed.

    Returns (theta_opt_rad, v_opt, alpha_opt_rad).

    Examples
    --------
    >>> import math
    >>> p = TwoDeflectorParams(
    ...     v_s=4.0, a_s=5.1, rho_a=1.225, D_s=0.895,
    ...     A_c=0.125, AR_c=6.0, D_h=0.9, rho_w=1000.0, A_h=0.0343,
    ... )
    >>> theta, v, alpha = optimal_angle(p)
    >>> 40 < math.degrees(theta) < 75
    True
    >>> 0 <= math.degrees(alpha) < 15
    True
    """
    theta_min = math.acos(p.D_s) + math.radians(1)
    theta_max = math.radians(89)
    thetas = np.linspace(theta_min, theta_max, n_grid)

    best_u, best_theta = -1.0, thetas[0]
    for theta in thetas:
        u = upwind_speed(float(theta), p)
        if u > best_u:
            best_u, best_theta = u, float(theta)

    sol = solve_equilibrium(best_theta, p)
    if sol is None:
        return best_theta, 0.0, 0.0
    v_opt, alpha_opt = sol
    return best_theta, v_opt, alpha_opt


