"""Dockerfile template engine for docker-avd-manager.

Templates live under ``templates/`` and use ``$PLACEHOLDER`` syntax
(``string.Template``). The engine renders them into concrete Dockerfiles that
are written next to the build context before ``docker build`` is invoked.
"""
from __future__ import annotations

import os
from string import Template
from typing import Dict

DEFAULT_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")


class TemplateEngine:
    def __init__(self, template_dir: str = DEFAULT_TEMPLATE_DIR):
        self.template_dir = os.path.abspath(template_dir)

    def list_templates(self) -> list[str]:
        if not os.path.isdir(self.template_dir):
            return []
        return sorted(
            f
            for f in os.listdir(self.template_dir)
            if f.endswith((".template", ".dockerfile", ".Dockerfile"))
        )

    def template_path(self, name: str) -> str:
        # Already a path or a full file name.
        if os.path.exists(name):
            return name
        candidate = os.path.join(self.template_dir, name)
        if os.path.exists(candidate):
            return candidate
        # Accept either a bare number ("33") or an "api33" shortcut and turn
        # it into the canonical Dockerfile.api33.template file name.
        if name.startswith("api") and name[3:].isdigit():
            suffix = name            # api33 -> Dockerfile.api33.template
        else:
            suffix = f"api{name}"    # 33    -> Dockerfile.api33.template
        shortcut = os.path.join(self.template_dir, f"Dockerfile.{suffix}.template")
        if os.path.exists(shortcut):
            return shortcut
        raise FileNotFoundError(f"template not found: {name}")

    def render(self, name: str, context: Dict[str, str]) -> str:
        path = self.template_path(name)
        with open(path, "r", encoding="utf-8") as fh:
            content = fh.read()
        return Template(content).safe_substitute(context)

    def render_to_file(self, name: str, context: Dict[str, str], dest: str) -> str:
        rendered = self.render(name, context)
        os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(rendered)
        return dest
