"""Device registry for docker-avd-manager.

Persists metadata about every AVD (Android Virtual Device) that has been
provisioned through the manager. The registry is a plain JSON file so it can
be inspected, backed up or edited by hand.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

from dataclasses import dataclass, asdict


@dataclass
class DeviceRecord:
    """A single AVD entry."""

    name: str
    api_level: int
    abi: str
    device: str
    resolution: str
    ram: str
    sdcard: str
    status: str = "stopped"          # stopped | running | building
    image_id: Optional[str] = None
    container_id: Optional[str] = None
    adb_port: Optional[int] = None
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "DeviceRecord":
        return cls(**data)


class Registry:
    """Loads / saves AVD records from a JSON file."""

    def __init__(self, path: Optional[str] = None):
        self.path = path or os.path.expanduser("~/.avd-manager/registry.json")
        self._devices: Dict[str, DeviceRecord] = {}
        self.load()

    # ------------------------------------------------------------------ I/O
    def load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as fh:
                    raw = json.load(fh)
                self._devices = {
                    name: DeviceRecord.from_dict(d)
                    for name, d in raw.get("devices", {}).items()
                }
            except (json.JSONDecodeError, TypeError):
                self._devices = {}
        else:
            self._devices = {}

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        payload = {
            "version": 1,
            "devices": {n: d.to_dict() for n, d in self._devices.items()},
        }
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)

    # ----------------------------------------------------------------- CRUD
    def add(self, record: DeviceRecord) -> None:
        now = datetime.now(timezone.utc).isoformat()
        if not record.created_at:
            record.created_at = now
        record.updated_at = now
        self._devices[record.name] = record
        self.save()

    def update(self, name: str, **changes) -> None:
        rec = self.get(name)
        if rec is None:
            raise KeyError(f"unknown device: {name}")
        for key, value in changes.items():
            if hasattr(rec, key):
                setattr(rec, key, value)
        rec.updated_at = datetime.now(timezone.utc).isoformat()
        self.save()

    def remove(self, name: str) -> None:
        self._devices.pop(name, None)
        self.save()

    def get(self, name: str) -> Optional[DeviceRecord]:
        return self._devices.get(name)

    def all(self) -> List[DeviceRecord]:
        return list(self._devices.values())

    def names(self) -> List[str]:
        return list(self._devices.keys())
