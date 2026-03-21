"""Unit tests for sailing_upwind.model.

Doctests in model.py cover the primary happy-path numbers.
These tests add boundary conditions, physics sanity checks, and
parameter sensitivity assertions.
"""

import math
import pytest

from sailing_upwind.model import (
    boat_speed,
    upwind_speed,
    no_go_threshold,
    optimal_angle,
    _cubic_roots,
)


# ---------------------------------------------------------------------------
# Shared fixture parameters (Laser Pico defaults)
# ---------------------------------------------------------------------------

PICO = dict(
    v_s=4.0,
    a_s=5.1,
    rho_a=1.225,
    D_s=0.895,
    D_h=0.9,
    rho_w=1000.0,
    A_h=0.0343,
)


# ---------------------------------------------------------------------------
# no_go_threshold
# ---------------------------------------------------------------------------

class TestNoGoThreshold:
    def test_ds_0_895(self):
        """arccos(0.895) ≈ 26.5° — close to the 26.2° quoted in coursework."""
        deg = math.degrees(no_go_threshold(0.895))
        assert abs(deg - 26.5) < 0.2

    def test_ds_0_9(self):
        """arccos(0.9) ≈ 25.8°."""
        deg = math.degrees(no_go_threshold(0.9))
        assert abs(deg - 25.8) < 0.2

    def test_ds_0_5_is_60_degrees(self):
        """arccos(0.5) = 60° exactly."""
        assert abs(math.degrees(no_go_threshold(0.5)) - 60.0) < 1e-9


# ---------------------------------------------------------------------------
# boat_speed
# ---------------------------------------------------------------------------

class TestBoatSpeed:
    def test_no_go_zone_returns_zero(self):
        """Angles inside the no-go zone produce zero boat speed."""
        for deg in [10, 15, 20, 25]:
            v = boat_speed(math.radians(deg), **PICO)
            assert v == 0.0, f"Expected 0 at {deg}°, got {v}"

    def test_exact_threshold_returns_zero(self):
        """At the exact no-go boundary the propulsive term is zero."""
        theta = no_go_threshold(PICO["D_s"])
        v = boat_speed(theta, **PICO)
        assert v == pytest.approx(0.0, abs=1e-10)

    def test_speed_positive_above_threshold(self):
        """Boat speed is positive at any valid sailing angle."""
        for deg in [30, 45, 57, 90, 120]:
            v = boat_speed(math.radians(deg), **PICO)
            assert v > 0, f"Expected positive speed at {deg}°"

    def test_speed_increases_with_wind(self):
        """Doubling wind speed should roughly double boat speed (v ∝ v_s)."""
        theta = math.radians(57)
        v1 = boat_speed(theta, **{**PICO, "v_s": 4.0})
        v2 = boat_speed(theta, **{**PICO, "v_s": 8.0})
        assert abs(v2 / v1 - 2.0) < 0.01

    def test_speed_increases_with_less_hull_drag(self):
        """D_h is the fraction of water speed *retained* by the hull.

        Higher D_h means the hull is more slippery (less energy lost to
        the water), so (1-D_h) in the denominator is smaller and boat
        speed is higher.
        """
        theta = math.radians(57)
        v_slippery_hull = boat_speed(theta, **{**PICO, "D_h": 0.95})
        v_draggy_hull = boat_speed(theta, **{**PICO, "D_h": 0.5})
        assert v_slippery_hull > v_draggy_hull

    def test_symmetry_port_and_starboard(self):
        """Speed should be the same on port and starboard tack (sin is symmetric)."""
        theta = math.radians(60)
        v_pos = boat_speed(theta, **PICO)
        v_neg = boat_speed(math.pi - theta, **{**PICO})
        # Note: pi - theta is the mirror angle; cos differs so this is a
        # different point — the real symmetry test is positive vs negative theta.
        # We use abs(sin) so treat negative angles:
        v_neg_tack = boat_speed(-theta, **PICO)
        assert v_pos == pytest.approx(v_neg_tack, rel=1e-9)

    def test_dimensions_give_ms(self):
        """Result must have units m/s — spot-check against a manual calculation."""
        # At 90° : v = sqrt(v_s^2 * a_s * rho_a * 1 * D_s / ((1-D_h)*rho_w*A_h))
        v_s, a_s, rho_a, D_s, D_h, rho_w, A_h = (
            4.0, 5.1, 1.225, 0.895, 0.9, 1000.0, 0.0343
        )
        expected = math.sqrt(
            v_s ** 2 * a_s * rho_a * 1.0 * D_s / ((1 - D_h) * rho_w * A_h)
        )
        got = boat_speed(math.pi / 2, v_s, a_s, rho_a, D_s, D_h, rho_w, A_h)
        assert got == pytest.approx(expected, rel=1e-9)


# ---------------------------------------------------------------------------
# upwind_speed
# ---------------------------------------------------------------------------

class TestUpwindSpeed:
    def test_relationship_to_boat_speed(self):
        """upwind_speed == boat_speed * cos(theta)."""
        theta = math.radians(57)
        v = boat_speed(theta, **PICO)
        u = upwind_speed(theta, **PICO)
        assert u == pytest.approx(v * math.cos(theta), rel=1e-9)

    def test_zero_in_no_go_zone(self):
        assert upwind_speed(math.radians(15), **PICO) == 0.0

    def test_zero_at_90_degrees(self):
        """cos(90°) = 0 so upwind component is 0 even though boat is moving."""
        u = upwind_speed(math.pi / 2, **PICO)
        assert u == pytest.approx(0.0, abs=1e-9)

    def test_maximum_is_near_optimal_angle(self):
        """Numerically verify that upwind speed peaks near optimal_angle."""
        opt_rad, _ = optimal_angle(PICO["D_s"])
        u_opt = upwind_speed(opt_rad, **PICO)
        # Sample neighbouring angles and check they are all <= u_opt
        for delta in [-0.05, -0.01, 0.01, 0.05]:
            u_nearby = upwind_speed(opt_rad + delta, **PICO)
            assert u_opt >= u_nearby - 1e-6, (
                f"upwind speed at optimal ({u_opt:.4f}) should be >= "
                f"at opt+{delta} ({u_nearby:.4f})"
            )


# ---------------------------------------------------------------------------
# optimal_angle
# ---------------------------------------------------------------------------

class TestOptimalAngle:
    def test_pico_defaults(self):
        """Coursework result: ~56.8° for D_s=0.895."""
        _, deg = optimal_angle(0.895)
        assert abs(deg - 56.8) < 0.5

    def test_ds_0_6(self):
        """Coursework example: D_s=0.6 → ~67.2°."""
        _, deg = optimal_angle(0.6)
        assert abs(deg - 67.2) < 0.5

    def test_ds_0_95(self):
        """For D_s=0.95 the cubic gives cos≈0.572 → 55.1°."""
        _, deg = optimal_angle(0.95)
        assert abs(deg - 55.1) < 0.5

    def test_lower_ds_means_larger_angle(self):
        """A slipperier sail allows sailing closer to the wind (larger angle)."""
        _, deg_low = optimal_angle(0.6)
        _, deg_high = optimal_angle(0.95)
        assert deg_low > deg_high

    def test_optimal_angle_above_no_go(self):
        """Optimal angle must be above the no-go threshold."""
        for D_s in [0.5, 0.7, 0.895, 0.95]:
            opt_rad, _ = optimal_angle(D_s)
            assert opt_rad > no_go_threshold(D_s)


# ---------------------------------------------------------------------------
# _cubic_roots — internal helper
# ---------------------------------------------------------------------------

class TestCubicRoots:
    def test_three_real_roots_for_ds_0_895(self):
        """The derivative cubic should have three real roots for typical D_s."""
        roots = _cubic_roots(0.895)
        assert len(roots) == 3

    def test_roots_satisfy_cubic(self):
        """Every returned root should actually satisfy the equation."""
        D_s = 0.895
        for x in _cubic_roots(D_s):
            residual = 4 * x**3 - 3 * D_s * x**2 - 3 * x + 2 * D_s
            assert abs(residual) < 1e-8, f"Root {x} has residual {residual}"
