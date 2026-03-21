"""Unit tests for sailing_upwind.config."""

import math
import pytest
from pathlib import Path

from sailing_upwind.config import load_config


class TestLoadConfig:
    def test_loads_default_config(self):
        cfg = load_config()
        assert cfg["wind"]["speed_ms"] == 4.0
        assert cfg["coefficients"]["D_s"] == pytest.approx(0.895)
        assert cfg["coefficients"]["D_h"] == pytest.approx(0.9)
        assert cfg["fluid"]["rho_air_kg_m3"] == pytest.approx(1.225)
        assert cfg["fluid"]["rho_water_kg_m3"] == pytest.approx(1000.0)
        assert cfg["boat"]["sail_area_m2"] == pytest.approx(5.1)
        assert cfg["boat"]["hull_area_m2"] == pytest.approx(0.0343)

    def test_invalid_ds_raises(self, tmp_path):
        bad = tmp_path / "bad.yaml"
        bad.write_text(
            "boat:\n  sail_area_m2: 5.1\n  hull_area_m2: 0.035\n"
            "wind:\n  speed_ms: 4.0\n"
            "coefficients:\n  D_s: 1.5\n  D_h: 0.9\n"
            "fluid:\n  rho_air_kg_m3: 1.225\n  rho_water_kg_m3: 1000.0\n"
        )
        with pytest.raises(ValueError, match="D_s"):
            load_config(bad)

    def test_invalid_dh_raises(self, tmp_path):
        bad = tmp_path / "bad.yaml"
        bad.write_text(
            "boat:\n  sail_area_m2: 5.1\n  hull_area_m2: 0.035\n"
            "wind:\n  speed_ms: 4.0\n"
            "coefficients:\n  D_s: 0.9\n  D_h: -0.1\n"
            "fluid:\n  rho_air_kg_m3: 1.225\n  rho_water_kg_m3: 1000.0\n"
        )
        with pytest.raises(ValueError, match="D_h"):
            load_config(bad)

    def test_missing_section_raises(self, tmp_path):
        bad = tmp_path / "bad.yaml"
        bad.write_text("boat:\n  sail_area_m2: 5.1\n  hull_area_m2: 0.035\n")
        with pytest.raises(ValueError, match="wind"):
            load_config(bad)

    def test_nonexistent_file_raises(self):
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path/to/config.yaml")
