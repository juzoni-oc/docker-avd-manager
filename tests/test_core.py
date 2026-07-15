"""Smoke tests for docker-avd-manager.

These tests exercise the registry and template engine without requiring Docker.
The manager gracefully records intents when ``docker`` is unavailable, so the
logic stays testable in CI.
"""
import os
import tempfile

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.registry import Registry, DeviceRecord
from src.template_engine import TemplateEngine
from src.manager import AVDManager


def test_registry_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "registry.json")
        reg = Registry(path=path)
        rec = DeviceRecord(
            name="t1", api_level=33, abi="x86_64", device="pixel_5",
            resolution="1080x2340", ram="2048M", sdcard="4096M",
        )
        reg.add(rec)
        reg.update("t1", status="running")
        # reload from disk
        reg2 = Registry(path=path)
        assert reg2.get("t1").status == "running"
        assert len(reg2.all()) == 1
        reg2.remove("t1")
        assert reg2.get("t1") is None


def test_template_render():
    engine = TemplateEngine()
    out = engine.render("api33", {
        "API_LEVEL": "33", "ABI": "x86_64", "DEVICE": "pixel_5",
        "RESOLUTION": "1080x2340", "RAM": "2048M", "SDCARD": "4096M",
        "AVD_NAME": "demo",
    })
    assert "android-33" in out
    assert "demo" in out


def test_manager_create_without_docker():
    with tempfile.TemporaryDirectory() as d:
        reg = Registry(path=os.path.join(d, "registry.json"))
        mgr = AVDManager(registry=reg)
        rec = mgr.create("emu", api_level=33)
        assert rec.name == "emu"
        assert reg.get("emu") is not None
        mgr.delete("emu")
        assert reg.get("emu") is None


if __name__ == "__main__":
    test_registry_roundtrip()
    test_template_render()
    test_manager_create_without_docker()
    print("all tests passed")
