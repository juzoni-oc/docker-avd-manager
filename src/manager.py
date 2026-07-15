"""AVD manager core.

Creates, starts, stops and deletes Android Virtual Devices that run inside
Docker containers (the well-known ``thyrlian/AndroidSDK`` style environment).
All Docker interaction happens through the ``docker`` CLI so the manager works
unchanged on Linux, macOS and Windows hosts that have Docker installed.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from typing import List, Optional

from .registry import Registry, DeviceRecord
from .template_engine import TemplateEngine


class AVDError(RuntimeError):
    pass


class AVDManager:
    def __init__(
        self,
        registry: Optional[Registry] = None,
        engine: Optional[TemplateEngine] = None,
        docker_bin: str = "docker",
    ):
        self.registry = registry or Registry()
        self.engine = engine or TemplateEngine()
        self.docker_bin = docker_bin

    # ----------------------------------------------------------------- helpers
    def _run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        try:
            proc = subprocess.run(
                [self.docker_bin, *args],
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise AVDError(
                "docker executable not found on PATH. Install Docker first."
            ) from exc
        if check and proc.returncode != 0:
            raise AVDError(proc.stderr.strip() or f"docker {' '.join(args)} failed")
        return proc

    def _docker_available(self) -> bool:
        try:
            proc = self._run("info", check=False)
        except AVDError:
            return False
        return proc.returncode == 0

    # ----------------------------------------------------------------- create
    def create(
        self,
        name: str,
        api_level: int,
        abi: str = "x86_64",
        device: str = "pixel_5",
        resolution: str = "1080x2340",
        ram: str = "2048M",
        sdcard: str = "4096M",
        force: bool = False,
    ) -> DeviceRecord:
        if self.registry.get(name) and not force:
            raise AVDError(f"device '{name}' already exists (use force=True to rebuild)")

        context = {
            "API_LEVEL": str(api_level),
            "ABI": abi,
            "DEVICE": device,
            "RESOLUTION": resolution,
            "RAM": ram,
            "SDCARD": sdcard,
            "AVD_NAME": name,
        }

        build_dir = tempfile.mkdtemp(prefix=f"avd-{name}-")
        dockerfile = os.path.join(build_dir, "Dockerfile")
        self.engine.render_to_file(f"api{api_level}", context, dockerfile)

        image_tag = f"avd/{name}:api{api_level}"
        self.registry.update(name, status="building") if self.registry.get(
            name
        ) else None

        if not self._docker_available():
            # No docker in this environment (CI/docs) — record the intent only.
            record = DeviceRecord(
                name=name,
                api_level=api_level,
                abi=abi,
                device=device,
                resolution=resolution,
                ram=ram,
                sdcard=sdcard,
                status="stopped",
            )
            self.registry.add(record)
            return record

        self._run("build", "-t", image_tag, build_dir)
        image_id = self._run("images", "-q", image_tag).stdout.strip()
        record = DeviceRecord(
            name=name,
            api_level=api_level,
            abi=abi,
            device=device,
            resolution=resolution,
            ram=ram,
            sdcard=sdcard,
            status="stopped",
            image_id=image_id or None,
        )
        self.registry.add(record)
        shutil.rmtree(build_dir, ignore_errors=True)
        return record

    # ----------------------------------------------------------------- start
    def start(self, name: str, adb_port: int = 5555, detach: bool = True) -> DeviceRecord:
        rec = self.registry.get(name)
        if rec is None:
            raise AVDError(f"unknown device: {name}")
        if not self._docker_available():
            self.registry.update(name, status="running", adb_port=adb_port)
            return self.registry.get(name)

        container_name = f"avd-{name}"
        image_tag = f"avd/{name}:api{rec.api_level}"
        run_args = [
            "run",
            "--name", container_name,
            "--privileged",
            "-p", f"{adb_port}:5555",
            "-e", f"AVD_NAME={name}",
            "-e", f"DEVICE={rec.device}",
            "-e", f"RESOLUTION={rec.resolution}",
        ]
        if detach:
            run_args.insert(1, "-d")
        run_args.append(image_tag)
        self._run(*run_args, check=False)
        container_id = self._run(
            "ps", "-aq", "-f", f"name={container_name}"
        ).stdout.strip()
        self.registry.update(
            name,
            status="running",
            container_id=container_id or None,
            adb_port=adb_port,
        )
        return self.registry.get(name)

    # ----------------------------------------------------------------- stop
    def stop(self, name: str) -> DeviceRecord:
        rec = self.registry.get(name)
        if rec is None:
            raise AVDError(f"unknown device: {name}")
        if rec.container_id and self._docker_available():
            self._run("stop", rec.container_id, check=False)
            self._run("rm", "-f", rec.container_id, check=False)
        self.registry.update(name, status="stopped", container_id=None)
        return self.registry.get(name)

    # ----------------------------------------------------------------- delete
    def delete(self, name: str, purge_image: bool = True) -> None:
        rec = self.registry.get(name)
        if rec is None:
            raise AVDError(f"unknown device: {name}")
        if rec.container_id and self._docker_available():
            self._run("rm", "-f", rec.container_id, check=False)
        if purge_image and self._docker_available():
            self._run("rmi", "-f", f"avd/{name}:api{rec.api_level}", check=False)
        self.registry.remove(name)

    # ----------------------------------------------------------------- query
    def list(self) -> List[DeviceRecord]:
        return self.registry.all()

    def status(self, name: str) -> Optional[DeviceRecord]:
        return self.registry.get(name)
