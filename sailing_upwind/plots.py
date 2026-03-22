"""Plotting helpers for the sailing upwind model."""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .model import boat_speed, upwind_speed, optimal_angle, no_go_threshold
from .config import load_config


def plot_upwind_speed(
    config_path: str | Path | None = None,
    show: bool = True,
    save: bool = False,
) -> None:
    """Plot boat speed and upwind component vs heading angle.

    Reads all parameters from the YAML config.

    Parameters
    ----------
    config_path:
        Path to an alternative config file.  Uses default if None.
    show:
        Display the interactive plot window.
    save:
        Save to the path specified in ``config.plot.output_file``.
    """
    cfg = load_config(config_path)

    v_s = cfg["wind"]["speed_ms"]
    a_s = cfg["boat"]["sail_area_m2"]
    A_h = cfg["boat"]["hull_area_m2"]
    D_s = cfg["coefficients"]["D_s"]
    D_h = cfg["coefficients"]["D_h"]
    rho_a = cfg["fluid"]["rho_air_kg_m3"]
    rho_w = cfg["fluid"]["rho_water_kg_m3"]

    theta_min = math.radians(cfg["plot"]["theta_min_deg"])
    theta_max = math.radians(cfg["plot"]["theta_max_deg"])
    n = cfg["plot"]["n_points"]
    thetas = np.linspace(theta_min, theta_max, n)

    threshold_deg = math.degrees(no_go_threshold(D_s))
    mode = cfg.get("model", {}).get("mode", "one_deflector")

    if mode == "two_deflector":
        from .two_deflector import (
            TwoDeflectorParams,
            solve_equilibrium as two_solve,
            optimal_angle as two_optimal_angle,
        )
        cb = cfg.get("model", {}).get("centreboard", {})
        p = TwoDeflectorParams(
            v_s=v_s, a_s=a_s, rho_a=rho_a, D_s=D_s,
            A_c=cb.get("area_m2", 0.125),
            AR_c=cb.get("aspect_ratio", 6.0),
            D_h=D_h, rho_w=rho_w, A_h=A_h,
        )
        sols = [two_solve(float(t), p) for t in thetas]
        speeds = [s[0] if s else 0.0 for s in sols]
        upwinds = [
            s[0] * math.cos(t + s[1]) if s else 0.0
            for s, t in zip(sols, thetas)
        ]
        theta_opt, v_opt, alpha_opt = two_optimal_angle(p)
        opt_deg = math.degrees(theta_opt)
        opt_upwind = v_opt * math.cos(theta_opt + alpha_opt)
        annotation = (
            f"max upwind\n{opt_upwind:.2f} m/s\n"
            f"({opt_upwind / 0.5144:.2f} kn)\n"
            f"leeway {math.degrees(alpha_opt):.1f}°"
        )
        title_suffix = "  (two-deflector)"
    else:
        speeds = [boat_speed(t, v_s, a_s, rho_a, D_s, D_h, rho_w, A_h) for t in thetas]
        upwinds = [upwind_speed(t, v_s, a_s, rho_a, D_s, D_h, rho_w, A_h) for t in thetas]
        opt_rad, opt_deg = optimal_angle(D_s)
        opt_upwind = upwind_speed(opt_rad, v_s, a_s, rho_a, D_s, D_h, rho_w, A_h)
        annotation = f"max upwind\n{opt_upwind:.2f} m/s\n({opt_upwind / 0.5144:.2f} kn)"
        title_suffix = ""

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(np.degrees(thetas), speeds, label="Boat speed (m/s)", color="steelblue")
    ax.plot(np.degrees(thetas), upwinds, label="Upwind component (m/s)", color="darkorange")
    ax.axvline(opt_deg, color="darkorange", linestyle="--", linewidth=1,
               label=f"Optimal angle = {opt_deg:.1f}°")
    ax.axvline(threshold_deg, color="grey", linestyle=":", linewidth=1,
               label=f"No-go threshold = {threshold_deg:.1f}°")
    ax.annotate(
        annotation,
        xy=(opt_deg, opt_upwind),
        xytext=(opt_deg + 10, opt_upwind + 0.1),
        arrowprops=dict(arrowstyle="->", color="black"),
        fontsize=9,
    )
    ax.set_xlabel("Heading angle from wind (degrees)")
    ax.set_ylabel("Speed (m/s)")
    ax.set_title(
        f"{cfg['boat']['name']} — wind {v_s} m/s  "
        f"(D_s={D_s}, D_h={D_h}){title_suffix}"
    )
    ax.legend()
    ax.set_xlim(0, 180)
    ax.set_ylim(bottom=0)
    fig.tight_layout()

    if save:
        out = cfg["plot"]["output_file"]
        fig.savefig(out, dpi=150)
        print(f"Saved plot to {out}")
    if show:
        plt.show()
    plt.close(fig)


def plot_ds_sensitivity(
    ds_values: list[float] | None = None,
    config_path: str | Path | None = None,
    show: bool = True,
    save: bool = False,
    output_file: str = "img/ds_sensitivity.png",
) -> None:
    """Plot optimal upwind speed for several D_s values.

    Parameters
    ----------
    ds_values:
        List of sail drag coefficients to compare.  Defaults to
        ``[0.6, 0.7, 0.8, 0.895, 0.95]``.
    config_path:
        Path to an alternative config file.
    show:
        Display the interactive plot window.
    save:
        Save the figure to *output_file*.
    output_file:
        Filename for saved figure.
    """
    if ds_values is None:
        ds_values = [0.6, 0.7, 0.8, 0.895, 0.95]

    cfg = load_config(config_path)
    v_s = cfg["wind"]["speed_ms"]
    a_s = cfg["boat"]["sail_area_m2"]
    A_h = cfg["boat"]["hull_area_m2"]
    D_h = cfg["coefficients"]["D_h"]
    rho_a = cfg["fluid"]["rho_air_kg_m3"]
    rho_w = cfg["fluid"]["rho_water_kg_m3"]

    thetas = np.linspace(0, math.pi, cfg["plot"]["n_points"])
    fig, ax = plt.subplots(figsize=(9, 5))

    for D_s in ds_values:
        upwinds = [upwind_speed(t, v_s, a_s, rho_a, D_s, D_h, rho_w, A_h) for t in thetas]
        opt_rad, opt_deg = optimal_angle(D_s)
        label = f"D_s={D_s}  (opt {opt_deg:.1f}°)"
        ax.plot(np.degrees(thetas), upwinds, label=label)

    ax.set_xlabel("Heading angle from wind (degrees)")
    ax.set_ylabel("Upwind component (m/s)")
    ax.set_title(f"Sensitivity to sail drag coefficient D_s  (wind {v_s} m/s)")
    ax.legend()
    ax.set_xlim(0, 180)
    ax.set_ylim(bottom=0)
    fig.tight_layout()

    if save:
        fig.savefig(output_file, dpi=150)
        print(f"Saved plot to {output_file}")
    if show:
        plt.show()
    plt.close(fig)
