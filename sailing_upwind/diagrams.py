"""Geometry and force diagrams for the one- and two-deflector models.

Four diagrams are produced:

* ``geometry_one_deflector``  — top-down view of boat, wind, heading, and the
  upwind progress component.
* ``geometry_two_deflector``  — same, adding the leeway angle and actual track.
* ``forces_one_deflector``    — force diagram for the one-deflector model.
* ``forces_two_deflector``    — force diagram for the two-deflector model.

All angles follow the standard convention used throughout the package:
  theta  — boat heading measured from the wind direction (radians)
  alpha  — leeway angle (radians, positive = drift to leeward)

Top-down orientation used in all geometry diagrams:
  +y  = upwind direction (wind blows in the -y direction, i.e. from top)
  +x  = starboard / to leeward (boat tacking on port, leeward to the right)
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Arc, Wedge


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _arrow(ax, x, y, dx, dy, color, lw=1.8, hw=0.055, hl=0.07):
    """Draw a filled arrow from (x,y) by vector (dx,dy)."""
    ax.annotate(
        "",
        xy=(x + dx, y + dy),
        xytext=(x, y),
        arrowprops=dict(
            arrowstyle=f"->,head_width={hw:.3f},head_length={hl:.3f}",
            color=color,
            lw=lw,
        ),
    )


def _force_arrow(ax, x, y, dx, dy, color, label: str, side: int = 1,
                 label_frac: float = 0.62, perp_dist: float = 0.10,
                 fontsize: int = 8, lw=1.8, hw=0.055, hl=0.07):
    """Arrow from (x,y) by (dx,dy) with label placed perpendicularly beside it.

    Parameters
    ----------
    side : +1 or -1
        Which side of the arrow to put the label (looking from tail to tip,
        +1 = left, -1 = right).
    label_frac : 0–1
        How far along the arrow length to anchor the label.
    perp_dist : float
        Perpendicular offset distance (axes units).
    """
    _arrow(ax, x, y, dx, dy, color, lw=lw, hw=hw, hl=hl)
    length = math.hypot(dx, dy)
    if length < 1e-9:
        return
    ux, uy = dx / length, dy / length          # unit along arrow
    px, py = -uy * side, ux * side             # unit perpendicular
    lx = x + dx * label_frac + px * perp_dist
    ly = y + dy * label_frac + py * perp_dist
    ax.text(lx, ly, label, color=color, fontsize=fontsize,
            ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.75))


def _dashed_arrow(ax, x, y, dx, dy, color, hw=0.055, hl=0.07, lw=1.3):
    ax.annotate(
        "",
        xy=(x + dx, y + dy),
        xytext=(x, y),
        arrowprops=dict(
            arrowstyle=f"->,head_width={hw:.3f},head_length={hl:.3f}",
            color=color, lw=lw, linestyle="dashed",
        ),
    )


def _angle_arc(ax, cx, cy, r, a1_deg, a2_deg, color,
               label: str | None = None, fontsize=8, r_label_frac=1.4,
               label_bbox=None):
    arc = Arc(
        (cx, cy), 2 * r, 2 * r,
        angle=0, theta1=min(a1_deg, a2_deg), theta2=max(a1_deg, a2_deg),
        color=color, lw=1.2,
    )
    ax.add_patch(arc)
    if label:
        mid = math.radians((a1_deg + a2_deg) / 2)
        kw = {} if label_bbox is None else {"bbox": label_bbox}
        ax.text(
            cx + r * r_label_frac * math.cos(mid),
            cy + r * r_label_frac * math.sin(mid),
            label, color=color, fontsize=fontsize, ha="center", va="center",
            **kw,
        )


def _boat_patch(ax, cx, cy, heading_rad, length=0.15, beam=0.045, color="dimgrey"):
    bx, by = math.sin(heading_rad), math.cos(heading_rad)
    sx, sy = by, -bx
    bow    = np.array([cx + bx * length / 2, cy + by * length / 2])
    stern  = np.array([cx - bx * length / 2, cy - by * length / 2])
    sb     = np.array([sx * beam / 2, sy * beam / 2])
    pts = np.array([bow, stern + sb, stern - sb, bow])
    ax.fill(pts[:, 0], pts[:, 1], color=color, alpha=0.7, zorder=3)
    ax.plot(pts[:, 0], pts[:, 1], color=color, lw=1, zorder=4)


# ---------------------------------------------------------------------------
# Geometry diagrams
# ---------------------------------------------------------------------------

def geometry_one_deflector(
    theta: float,
    show: bool = True,
    save: bool = False,
    output_file: str = "img/geometry_one_deflector.svg",
) -> None:
    """Top-down geometry diagram for the one-deflector model."""
    theta_deg = math.degrees(theta)
    bx, by = math.sin(theta), math.cos(theta)

    fig, ax = plt.subplots(figsize=(4.2, 3.4))
    ax.set_aspect("equal")
    ax.axis("off")

    cx, cy = 0.0, -0.05

    # Wind arrows — compact strip at top
    for xw in (-0.45, -0.15, 0.15, 0.45):
        _arrow(ax, xw, 0.62, 0, -0.34, color="#5b9bd5", hw=0.04, hl=0.05)
    ax.text(-0.58, 0.45, "wind", color="#5b9bd5", fontsize=8, va="center")

    # Heading vector
    L = 0.52
    _arrow(ax, cx, cy, bx * L, by * L, color="dimgrey", hw=0.055, hl=0.07)
    ax.text(cx + bx * L * 1.16, cy + by * L * 1.13,
            f"heading ($\\theta={theta_deg:.0f}°$)",
            color="dimgrey", fontsize=8, ha="center", va="center")

    # Upwind component — dashed grey projection of heading; label at tip
    ax.annotate("", xy=(cx, cy + by * L), xytext=(cx, cy),
                arrowprops=dict(arrowstyle="->,head_width=0.05,head_length=0.065",
                                color="dimgrey", lw=1.4, linestyle="dashed"))
    ax.text(cx + 0.14, cy + by * L * 0.18,
            "$u = v\\cos\\theta$", color="dimgrey", fontsize=8, ha="left", va="center")

    # Theta arc — label placed just outside the arc at the bisector
    _angle_arc(ax, cx, cy, 0.26, a1_deg=90, a2_deg=90 - theta_deg,
               color="dimgrey", label="$\\theta$", fontsize=8, r_label_frac=1.10)

    # Boat
    _boat_patch(ax, cx, cy, heading_rad=theta)

    # No-go zone
    nogo_deg = 26.5
    wedge = Wedge((cx, cy), 0.62, 90 - nogo_deg, 90 + nogo_deg,
                  color="#e74c3c", alpha=0.09)
    ax.add_patch(wedge)
    ax.text(cx, cy + 0.55, "no-go", color="#e74c3c", fontsize=7,
            ha="center", va="bottom", alpha=0.9)

    ax.set_xlim(-0.72, 0.82)
    ax.set_ylim(cy - 0.18, 0.70)

    fig.tight_layout(pad=0.2)
    if save:
        Path(output_file).parent.mkdir(exist_ok=True)
        fig.savefig(output_file, format="svg", bbox_inches="tight")
        print(f"Saved {output_file}")
    if show:
        plt.show()
    plt.close(fig)


def geometry_two_deflector(
    theta: float,
    alpha: float,
    show: bool = True,
    save: bool = False,
    output_file: str = "img/geometry_two_deflector.svg",
) -> None:
    """Top-down geometry diagram for the two-deflector model."""
    theta_deg  = math.degrees(theta)
    alpha_deg  = math.degrees(alpha)
    track_rad  = theta + alpha
    track_deg  = theta_deg + alpha_deg
    bx, by     = math.sin(theta), math.cos(theta)
    tx, ty     = math.sin(track_rad), math.cos(track_rad)

    fig, ax = plt.subplots(figsize=(4.6, 3.5))
    ax.set_aspect("equal")
    ax.axis("off")

    cx, cy = 0.0, -0.05

    # Wind arrows
    for xw in (-0.45, -0.15, 0.15, 0.45):
        _arrow(ax, xw, 0.62, 0, -0.34, color="#5b9bd5", hw=0.04, hl=0.05)
    ax.text(-0.58, 0.45, "wind", color="#5b9bd5", fontsize=8, va="center")

    L = 0.52

    # Heading vector (grey) — label offset CCW (left of arrow) at short radius
    _arrow(ax, cx, cy, bx * L, by * L, color="dimgrey", hw=0.05, hl=0.065)
    ax.text(cx + bx * L * 1.08 - by * 0.13, cy + by * L * 1.08 + bx * 0.13 - 0.07,
            f"heading ($\\theta={theta_deg:.0f}°$)",
            color="dimgrey", fontsize=8, ha="center", va="center")

    # Track vector (green) — label offset CW (right of arrow) at longer radius
    _arrow(ax, cx, cy, tx * L, ty * L, color="seagreen", hw=0.05, hl=0.065)
    ax.text(cx + tx * L * 1.28 + ty * 0.10, cy + ty * L * 1.28 - tx * 0.10 - 0.07,
            f"track ($\\theta+\\alpha={track_deg:.0f}°$)",
            color="seagreen", fontsize=8, ha="center", va="center")

    # Upwind component — dashed grey projection of track vector; label at tip
    ax.annotate("", xy=(cx, cy + ty * L), xytext=(cx, cy),
                arrowprops=dict(arrowstyle="->,head_width=0.05,head_length=0.065",
                                color="dimgrey", lw=1.4, linestyle="dashed"))
    ax.text(cx + 0.14, cy + ty * L * 0.18,
            "$u = v\\cos(\\theta+\\alpha)$", color="dimgrey", fontsize=7.5, ha="left", va="center")

    # Arcs — label placed just outside arc
    _angle_arc(ax, cx, cy, 0.22, a1_deg=90, a2_deg=90 - theta_deg,
               color="dimgrey", label="$\\theta$", fontsize=8, r_label_frac=1.10)
    _angle_arc(ax, cx, cy, 0.43, a1_deg=90 - theta_deg, a2_deg=90 - track_deg,
               color="seagreen", label="$\\alpha$", fontsize=8, r_label_frac=1.10,
               label_bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))

    # Boat
    _boat_patch(ax, cx, cy, heading_rad=theta)

    # No-go zone
    wedge = Wedge((cx, cy), 0.62, 90 - 26.5, 90 + 26.5,
                  color="#e74c3c", alpha=0.09)
    ax.add_patch(wedge)
    ax.text(cx, cy + 0.55, "no-go", color="#e74c3c", fontsize=7,
            ha="center", va="bottom", alpha=0.9)

    ax.set_xlim(-0.72, 0.92)
    ax.set_ylim(cy - 0.18, 0.70)

    fig.tight_layout(pad=0.2)
    if save:
        Path(output_file).parent.mkdir(exist_ok=True)
        fig.savefig(output_file, format="svg", bbox_inches="tight")
        print(f"Saved {output_file}")
    if show:
        plt.show()
    plt.close(fig)


# ---------------------------------------------------------------------------
# Force diagrams
# ---------------------------------------------------------------------------

def forces_one_deflector(
    theta: float,
    v_s: float,
    a_s: float,
    rho_a: float,
    D_s: float,
    D_h: float,
    rho_w: float,
    A_h: float,
    v: float,
    show: bool = True,
    save: bool = False,
    output_file: str = "img/forces_one_deflector.svg",
) -> None:
    """Force diagram for the one-deflector model."""
    sin_t, cos_t = math.sin(theta), math.cos(theta)
    F_sail_x = rho_a * a_s * v_s**2 * abs(sin_t) * (D_s - cos_t)
    F_sail_y = rho_a * a_s * v_s**2 * sin_t**2
    F_hull   = (1 - D_h) * rho_w * A_h * v**2

    F_max = max(F_sail_x, F_sail_y, F_hull)
    sc = 0.42 / F_max if F_max > 0 else 1.0

    fwd = np.array([sin_t, cos_t])
    lee = np.array([cos_t, -sin_t])

    fig, ax = plt.subplots(figsize=(4.4, 3.8))
    ax.set_aspect("equal")
    ax.axis("off")

    cx, cy = 0.0, 0.0

    _boat_patch(ax, cx, cy, heading_rad=theta, length=0.18, beam=0.055)

    def _tip_label(dx, dy, label, color):
        ln = math.hypot(dx, dy)
        ux, uy = (dx / ln, dy / ln) if ln > 1e-9 else (0.0, 1.0)
        reach = max(ln + 0.08, 0.30)
        ax.text(cx + ux * reach, cy + uy * reach, label,
                color=color, fontsize=8, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))

    # F_sail_x — forward
    d = fwd * F_sail_x * sc
    _arrow(ax, cx, cy, d[0], d[1], color="steelblue")
    _tip_label(d[0], d[1], f"$F_{{\\rm sail,x}}$  {F_sail_x:.1f} N", "steelblue")

    # F_hull — aft
    d2 = -fwd * F_hull * sc
    _arrow(ax, cx, cy, d2[0], d2[1], color="#e74c3c")
    _tip_label(d2[0], d2[1], f"$F_{{\\rm hull}}$  {F_hull:.1f} N", "#e74c3c")

    # F_sail_y — leeward (dashed, cancelled)
    d3 = lee * F_sail_y * sc
    _dashed_arrow(ax, cx, cy, d3[0], d3[1], color="grey")
    _tip_label(d3[0], d3[1], f"$F_{{\\rm sail,y}}$  {F_sail_y:.1f} N\n(cancelled)", "grey")

    # Centreboard reaction — windward (dashed)
    d4 = -lee * F_sail_y * sc
    _dashed_arrow(ax, cx, cy, d4[0], d4[1], color="grey")
    _tip_label(d4[0], d4[1], f"$F_{{\\rm cb}}$  {F_sail_y:.1f} N\n(reaction)", "grey")

    # Wind indicator — small, top-left; label below arrowhead
    _arrow(ax, -0.45, 0.38, 0, -0.14, color="#5b9bd5", hw=0.035, hl=0.045)
    ax.text(-0.45, 0.18, "wind", color="#5b9bd5", fontsize=7.5, ha="center")

    ax.set_xlim(-0.65, 0.65)
    ax.set_ylim(-0.65, 0.65)

    if save:
        Path(output_file).parent.mkdir(exist_ok=True)
        fig.savefig(output_file, format="svg", bbox_inches="tight")
        print(f"Saved {output_file}")
    if show:
        plt.show()
    plt.close(fig)


def forces_two_deflector(
    theta: float,
    alpha: float,
    v_s: float,
    a_s: float,
    rho_a: float,
    D_s: float,
    v: float,
    A_c: float,
    AR_c: float,
    rho_w: float,
    A_h: float,
    D_h: float,
    show: bool = True,
    save: bool = False,
    output_file: str = "img/forces_two_deflector.svg",
) -> None:
    """Force diagram for the two-deflector model."""
    sin_t, cos_t = math.sin(theta), math.cos(theta)
    F_sail_x = rho_a * a_s * v_s**2 * abs(sin_t) * (D_s - cos_t)
    F_sail_y = rho_a * a_s * v_s**2 * sin_t**2
    CL = 2.0 * math.pi * math.sin(alpha)
    CD = CL**2 / (math.pi * AR_c)
    q  = 0.5 * rho_w * A_c * v**2
    F_cb_lift = q * CL
    F_cb_drag = q * CD
    F_hull    = (1 - D_h) * rho_w * A_h * v**2

    F_max = max(F_sail_x, F_sail_y, F_hull, F_cb_lift, F_cb_drag)
    sc = 0.42 / F_max if F_max > 0 else 1.0

    fwd = np.array([sin_t, cos_t])
    lee = np.array([cos_t, -sin_t])

    fig, ax = plt.subplots(figsize=(4.6, 4.0))
    ax.set_aspect("equal")
    ax.axis("off")

    cx, cy = 0.0, 0.0

    _boat_patch(ax, cx, cy, heading_rad=theta, length=0.18, beam=0.055)

    def _tip_label(dx, dy, label, color):
        """Place label just beyond the arrowhead, minimum 0.30 from origin."""
        ln = math.hypot(dx, dy)
        ux, uy = (dx / ln, dy / ln) if ln > 1e-9 else (0.0, 1.0)
        reach = max(ln + 0.08, 0.30)
        ax.text(cx + ux * reach, cy + uy * reach, label,
                color=color, fontsize=7.5, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))

    # F_sail_x — forward
    d = fwd * F_sail_x * sc
    _arrow(ax, cx, cy, d[0], d[1], color="steelblue")
    _tip_label(d[0], d[1], f"$F_{{\\rm sail,x}}$  {F_sail_x:.1f} N", "steelblue")

    # F_sail_y — leeward
    d2 = lee * F_sail_y * sc
    _arrow(ax, cx, cy, d2[0], d2[1], color="#9b59b6")
    _tip_label(d2[0], d2[1], f"$F_{{\\rm sail,y}}$  {F_sail_y:.1f} N", "#9b59b6")

    # F_cb_lift — windward
    d3 = -lee * F_cb_lift * sc
    _arrow(ax, cx, cy, d3[0], d3[1], color="seagreen")
    _tip_label(d3[0], d3[1], f"$F_{{\\rm cb,lift}}$  {F_cb_lift:.1f} N", "seagreen")

    # Combined aft drag
    d4 = -fwd * (F_hull + F_cb_drag) * sc
    _arrow(ax, cx, cy, d4[0], d4[1], color="#e74c3c")
    _tip_label(d4[0], d4[1], f"$F_{{\\rm hull}}+F_{{\\rm cb,drag}}$  {F_hull+F_cb_drag:.1f} N", "#e74c3c")

    # Leeway arc
    _angle_arc(ax, cx, cy, 0.25,
               a1_deg=90 - math.degrees(theta),
               a2_deg=90 - math.degrees(theta + alpha),
               color="seagreen", label=f"$\\alpha={math.degrees(alpha):.1f}°$",
               fontsize=8, r_label_frac=1.55)

    # Wind indicator; label below arrowhead
    _arrow(ax, -0.45, 0.38, 0, -0.14, color="#5b9bd5", hw=0.035, hl=0.045)
    ax.text(-0.45, 0.18, "wind", color="#5b9bd5", fontsize=7.5, ha="center")

    ax.set_xlim(-0.65, 0.65)
    ax.set_ylim(-0.65, 0.65)

    if save:
        Path(output_file).parent.mkdir(exist_ok=True)
        fig.savefig(output_file, format="svg", bbox_inches="tight")
        print(f"Saved {output_file}")
    if show:
        plt.show()
    plt.close(fig)


# ---------------------------------------------------------------------------
# Convenience wrapper — generate all four diagrams from config
# ---------------------------------------------------------------------------

def plot_all_diagrams(
    config_path=None,
    show: bool = True,
    save: bool = False,
) -> None:
    """Generate all four diagrams using parameters from the YAML config.

    The optimal heading (and, for the two-deflector model, leeway) is computed
    automatically so the diagrams always reflect the current config values.
    """
    from .config import load_config
    from .model import optimal_angle as opt1, boat_speed
    from .two_deflector import TwoDeflectorParams, optimal_angle as opt2

    cfg = load_config(config_path)
    v_s   = cfg["wind"]["speed_ms"]
    a_s   = cfg["boat"]["sail_area_m2"]
    A_h   = cfg["boat"]["hull_area_m2"]
    D_s   = cfg["coefficients"]["D_s"]
    D_h   = cfg["coefficients"]["D_h"]
    rho_a = cfg["fluid"]["rho_air_kg_m3"]
    rho_w = cfg["fluid"]["rho_water_kg_m3"]
    cb    = cfg.get("model", {}).get("centreboard", {})
    A_c   = cb.get("area_m2", 0.125)
    AR_c  = cb.get("aspect_ratio", 6.0)

    theta1_rad, _ = opt1(D_s)
    v1 = boat_speed(theta1_rad, v_s, a_s, rho_a, D_s, D_h, rho_w, A_h)

    p = TwoDeflectorParams(
        v_s=v_s, a_s=a_s, rho_a=rho_a, D_s=D_s,
        A_c=A_c, AR_c=AR_c, D_h=D_h, rho_w=rho_w, A_h=A_h,
    )
    theta2_rad, v2, alpha2_rad = opt2(p)

    geometry_one_deflector(theta1_rad, show=show, save=save)
    geometry_two_deflector(theta2_rad, alpha2_rad, show=show, save=save)
    forces_one_deflector(
        theta=theta1_rad, v_s=v_s, a_s=a_s, rho_a=rho_a,
        D_s=D_s, D_h=D_h, rho_w=rho_w, A_h=A_h, v=v1,
        show=show, save=save,
    )
    forces_two_deflector(
        theta=theta2_rad, alpha=alpha2_rad,
        v_s=v_s, a_s=a_s, rho_a=rho_a, D_s=D_s, v=v2,
        A_c=A_c, AR_c=AR_c, rho_w=rho_w, A_h=A_h, D_h=D_h,
        show=show, save=save,
    )


