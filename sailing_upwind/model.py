"""Core physics model for sailing upwind.

All angles are in **radians** unless stated otherwise.

Model assumptions (from coursework):
- Close-hauled: sail lies along the boat's centre-line.
- No air resistance on the hull.
- Wind is a uniform flow; no variation with height.
- Infinite lateral resistance (perfect centre-board); no lateral drift.
- Flat sail.
- Sail redirects passing air to its own direction.
- Sail slows air by a uniform scalar factor D_s (sail drag coefficient).
- Hull drag force = (1 - D_h) * rho_w * A_h * v^2  where D_h is the
  fraction of water speed *retained* after passing the hull.

Key equations
-------------
Momentum flux of wind column hitting sail per second::

    Upsilon = v_s^2 * a_s * rho_a * |sin(theta)|

Forward (propulsive) force from sail::

    F_sail = Upsilon * (D_s - cos(theta))

Hull drag force at boat speed v::

    F_drag = (1 - D_h) * rho_w * A_h * v^2

Terminal boat speed (F_sail = F_drag)::

    v = sqrt( v_s^2 * a_s * rho_a * |sin(theta)| * (D_s - cos(theta))
              / ((1 - D_h) * rho_w * A_h) )

Upwind component of boat speed::

    u = v * cos(theta)

The optimal angle satisfies the cubic (x = cos(theta))::

    4x^3 - 3*D_s*x^2 - 3x + 2*D_s = 0

NOTE ON A BUG IN THE ORIGINAL COURSEWORK
-----------------------------------------
The derivation correctly writes the drag as ``(1-D_h)*rho_w*A_h*v^2`` but
the final printed formula drops the ``(1-)`` and writes ``D_h*rho_w*A_h``.
This module uses the *correct* form ``(1-D_h)`` throughout.
"""

from __future__ import annotations

import math
from typing import Tuple

import numpy as np


# ---------------------------------------------------------------------------
# Physical formulae
# ---------------------------------------------------------------------------

def boat_speed(
    theta: float,
    v_s: float,
    a_s: float,
    rho_a: float,
    D_s: float,
    D_h: float,
    rho_w: float,
    A_h: float,
) -> float:
    """Return terminal boat speed (m/s) at angle *theta* from the wind.

    Parameters
    ----------
    theta:
        Angle between boat heading and wind direction (radians).
        Must be in the range (arccos(D_s), pi].
    v_s:
        True wind speed (m/s).
    a_s:
        Sail area (m^2).
    rho_a:
        Density of air (kg/m^3).
    D_s:
        Sail drag coefficient (dimensionless, 0 < D_s < 1).
        Fraction of wind speed retained after passing over the sail.
    D_h:
        Hull drag coefficient (dimensionless, 0 < D_h < 1).
        Fraction of water speed retained after passing the hull.
    rho_w:
        Density of water (kg/m^3).
    A_h:
        Frontal underwater hull area (m^2).

    Returns
    -------
    float
        Terminal boat speed in m/s, or 0.0 when the angle is inside the
        no-go zone (D_s - cos(theta) <= 0).

    Examples
    --------
    >>> import math
    >>> v = boat_speed(
    ...     theta=math.radians(56.8),
    ...     v_s=4.0, a_s=5.1, rho_a=1.225,
    ...     D_s=0.895, D_h=0.9, rho_w=1000.0, A_h=0.0343,
    ... )
    >>> round(v, 2)
    2.91

    Inside the no-go zone the propulsive force is zero or negative:
    >>> boat_speed(
    ...     theta=math.radians(20.0),
    ...     v_s=4.0, a_s=5.1, rho_a=1.225,
    ...     D_s=0.895, D_h=0.9, rho_w=1000.0, A_h=0.0343,
    ... )
    0.0
    """
    propulsive = D_s - math.cos(theta)
    if propulsive <= 0.0:
        return 0.0
    numerator = v_s ** 2 * a_s * rho_a * abs(math.sin(theta)) * propulsive
    denominator = (1.0 - D_h) * rho_w * A_h
    return math.sqrt(numerator / denominator)


def upwind_speed(
    theta: float,
    v_s: float,
    a_s: float,
    rho_a: float,
    D_s: float,
    D_h: float,
    rho_w: float,
    A_h: float,
) -> float:
    """Return the upwind component of boat velocity (m/s).

    This is ``boat_speed(theta, ...) * cos(theta)``.

    Examples
    --------
    >>> import math
    >>> u = upwind_speed(
    ...     theta=math.radians(56.8),
    ...     v_s=4.0, a_s=5.1, rho_a=1.225,
    ...     D_s=0.895, D_h=0.9, rho_w=1000.0, A_h=0.0343,
    ... )
    >>> round(u, 2)
    1.59
    """
    return boat_speed(theta, v_s, a_s, rho_a, D_s, D_h, rho_w, A_h) * math.cos(theta)


def no_go_threshold(D_s: float) -> float:
    """Minimum angle from wind at which sailing is physically possible (radians).

    Below this angle D_s - cos(theta) <= 0 and no forward force is generated.

    Parameters
    ----------
    D_s:
        Sail drag coefficient (0 < D_s < 1).

    Returns
    -------
    float
        Threshold angle in radians.

    Examples
    --------
    >>> import math
    >>> round(math.degrees(no_go_threshold(0.895)), 1)
    26.5
    >>> round(math.degrees(no_go_threshold(0.9)), 1)
    25.8
    """
    return math.acos(D_s)


def _cubic_roots(D_s: float) -> list[float]:
    """Return real roots of  4x^3 - 3*D_s*x^2 - 3x + 2*D_s = 0.

    The roots are values of cos(theta) at the stationary points of the
    upwind speed function.

    Examples
    --------
    >>> roots = _cubic_roots(0.895)
    >>> [round(r, 3) for r in sorted(roots)]
    [-0.844, 0.547, 0.969]
    """
    # coefficients in descending power order: 4, -3*D_s, -3, 2*D_s
    coeffs = [4.0, -3.0 * D_s, -3.0, 2.0 * D_s]
    roots = np.roots(coeffs)
    return [float(r.real) for r in roots if abs(r.imag) < 1e-9]


def optimal_angle(D_s: float) -> Tuple[float, float]:
    """Return the optimum angle to sail upwind (radians, degrees).

    Finds the physically meaningful maximum of the upwind speed function.
    The optimum is the root of the derivative cubic with
    ``arccos(D_s) < theta < pi/2`` (i.e. cos(theta) in (0, D_s)).

    Parameters
    ----------
    D_s:
        Sail drag coefficient.

    Returns
    -------
    (theta_rad, theta_deg)
        Optimal angle in radians and degrees.

    Examples
    --------
    >>> rad, deg = optimal_angle(0.895)
    >>> round(deg, 1)
    56.8
    >>> rad2, deg2 = optimal_angle(0.6)
    >>> round(deg2, 1)
    67.2
    >>> rad3, deg3 = optimal_angle(0.95)
    >>> round(deg3, 1)
    55.1
    """
    min_cos = 0.0          # cos(90°) – beyond 90° we're not going upwind
    max_cos = D_s          # below no-go threshold
    roots = _cubic_roots(D_s)
    candidates = [r for r in roots if min_cos < r < max_cos]
    if not candidates:
        raise ValueError(f"No valid optimum found for D_s={D_s}")
    # There should be exactly one root in this range; take the largest cos
    # (smallest angle) as it gives the upwind maximum.
    best_cos = max(candidates)
    theta = math.acos(best_cos)
    return theta, math.degrees(theta)
