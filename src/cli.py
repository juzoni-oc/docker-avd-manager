#!/usr/bin/env python3
"""Command line interface for docker-avd-manager."""
from __future__ import annotations

import argparse
import sys

from .manager import AVDManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="avd-manager",
        description="Manage Android Virtual Devices inside Docker.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create", help="create a new AVD")
    p_create.add_argument("name")
    p_create.add_argument("--api", type=int, required=True, help="Android API level (30-34)")
    p_create.add_argument("--abi", default="x86_64")
    p_create.add_argument("--device", default="pixel_5")
    p_create.add_argument("--resolution", default="1080x2340")
    p_create.add_argument("--ram", default="2048M")
    p_create.add_argument("--sdcard", default="4096M")
    p_create.add_argument("--force", action="store_true")

    p_start = sub.add_parser("start", help="start an AVD container")
    p_start.add_argument("name")
    p_start.add_argument("--adb-port", type=int, default=5555)

    p_stop = sub.add_parser("stop", help="stop an AVD container")
    p_stop.add_argument("name")

    p_delete = sub.add_parser("delete", help="delete an AVD")
    p_delete.add_argument("name")
    p_delete.add_argument("--keep-image", action="store_true")

    p_list = sub.add_parser("list", help="list AVDs")

    p_status = sub.add_parser("status", help="show AVD status")
    p_status.add_argument("name")

    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    mgr = AVDManager()

    if args.command == "create":
        rec = mgr.create(
            args.name,
            args.api,
            abi=args.abi,
            device=args.device,
            resolution=args.resolution,
            ram=args.ram,
            sdcard=args.sdcard,
            force=args.force,
        )
        print(f"created AVD '{rec.name}' (API {rec.api_level}, {rec.resolution})")
    elif args.command == "start":
        rec = mgr.start(args.name, adb_port=args.adb_port)
        print(f"started '{rec.name}' -> adb tcp:localhost:{rec.adb_port}")
    elif args.command == "stop":
        mgr.stop(args.name)
        print(f"stopped '{args.name}'")
    elif args.command == "delete":
        mgr.delete(args.name, purge_image=not args.keep_image)
        print(f"deleted '{args.name}'")
    elif args.command == "list":
        recs = mgr.list()
        if not recs:
            print("no AVDs registered")
        for r in recs:
            print(f"{r.name:20s} API {r.api_level}  {r.status:9s} {r.resolution}")
    elif args.command == "status":
        r = mgr.status(args.name)
        if r is None:
            print(f"unknown device: {args.name}")
            return 1
        for k, v in r.to_dict().items():
            print(f"{k:14s}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
