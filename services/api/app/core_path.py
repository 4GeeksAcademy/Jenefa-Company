"""Ensure the shared scripts/incident_core package is importable."""

from __future__ import annotations

import sys
from pathlib import Path

# The API is commonly started from the repository root as
# ``services.api.app.main`` while older modules import the package as ``app``.
# Register one canonical package object before those modules are imported;
# otherwise SQLModel sees duplicate model classes and attempts to register the
# same tables twice.
if __name__.startswith("services.api.app."):
    import services.api.app as _api_package

    sys.modules.setdefault("app", _api_package)
    for _subpackage in ("inventory", "telemetry", "auth"):
        _module_name = f"services.api.app.{_subpackage}"
        _module = __import__(_module_name, fromlist=[_subpackage])
        sys.modules.setdefault(f"app.{_subpackage}", _module)

_SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
