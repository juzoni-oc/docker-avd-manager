# docker-avd-manager

> Manage **Android Virtual Devices (AVD)** inside Docker containers — create,
> start, stop and delete emulators on demand, with per-API-level Dockerfile
> templates (API 30–34).

`docker-avd-manager` turns a single host into a pool of disposable Android
emulators. Each AVD is built from a parameterized Dockerfile template and runs
the official Android emulator in headless (`-no-window`) mode, exposing ADB
over TCP. The registry keeps track of every virtual device so you can script
CI pipelines, device farms or local testing without leaving your terminal.

## Features

- 🐳 Build AVD images from `string.Template` Dockerfiles (API 30–34).
- 📋 Persistent JSON **registry** of all provisioned devices.
- 🚦 `create` / `start` / `stop` / `delete` / `list` / `status` commands.
- 🔌 ADB exposed over TCP (`-p <host>:<5555>`), ready for `adb connect`.
- 🧩 Pluggable template engine — drop a new `Dockerfile.apiXX.template` and it
  is picked up automatically.

## Requirements

- Python 3.8+
- [Docker](https://docs.docker.com/get-docker/) installed and running
- (On the host inside the container) Android SDK / emulator images

## Install

```bash
pip install -e .
avd-manager --help
```

Or run it directly from source:

```bash
python -m src.cli --help
```

## Quick start

```bash
# Create an emulator running API 33 (Pixel 5 skin, 1080x2340)
python -m src.cli create pixel13 --api 33 --device pixel_5 --resolution 1080x2340

# Start it and forward ADB to localhost:5555
python -m src.cli start pixel13 --adb-port 5555

# From another shell
adb connect localhost:5555
adb devices

# Stop and remove it
python -m src.cli stop pixel13
python -m src.cli delete pixel13
```

## Project layout

```
docker-avd-manager/
├── src/
│   ├── manager.py          # AVD manager core (create/delete/start/stop)
│   ├── template_engine.py  # Dockerfile template engine
│   ├── registry.py         # device registry (JSON backed)
│   └── cli.py              # command line interface
├── templates/
│   └── Dockerfile.api30..34.template
├── Dockerfile.template     # base template
├── requirements.txt
└── README.md
```

## Configuration knobs

| Option        | Default     | Meaning                         |
|---------------|-------------|---------------------------------|
| `--api`       | —           | Android API level (30–34)       |
| `--abi`       | `x86_64`    | System image ABI                |
| `--device`    | `pixel_5`   | AVD device profile              |
| `--resolution`| `1080x2340` | Emulator skin resolution        |
| `--ram`       | `2048M`     | RAM allocated to the emulator   |
| `--sdcard`    | `4096M`     | SD card size                    |

## Contact

Maintained by **juzoni-oc**. For commercial cloud-device / emulator hosting,
custom ROM builds and device-farm integrations, reach out via
**[qtphone.com](https://qtphone.com)**.

## License

MIT
