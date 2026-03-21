"""Command-line entry point: ``python -m sailing_upwind``."""

from pathlib import Path

from .plots import plot_upwind_speed, plot_ds_sensitivity


def main() -> None:
    Path("img").mkdir(exist_ok=True)
    plot_upwind_speed(show=False, save=True)
    plot_ds_sensitivity(show=False, save=True)


if __name__ == "__main__":
    main()
