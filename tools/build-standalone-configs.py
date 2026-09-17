#!/usr/bin/env python3
"""Generate self-contained ESPHome configs for the ESPHome dashboard.

The room files in esphome/ use `packages: !include`, which is good for local
editing but awkward in the dashboard, where every device wants one flat file.
This script resolves the include and writes one complete file per room.

Edit ROOMS below to match your own units, then run:

    python3 tools/build-standalone-configs.py

Output goes to esphome/dashboard/ (git-ignored by default -- it is generated).
"""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = ROOT / "esphome" / "packages" / "remko-xye-base.yaml"
TARGET = ROOT / "esphome" / "dashboard"

# (slug, display name) -- one entry per indoor unit.
ROOMS = [
    ("livingroom", "Living room"),
    ("bedroom", "Bedroom"),
    ("study", "Study"),
]

HEADER = """# =============================================================================
#  {room} -- self-contained config for the ESPHome dashboard
# -----------------------------------------------------------------------------
#  GENERATED from esphome/packages/remko-xye-base.yaml -- do not edit here.
#  Make changes in the package, then re-run:
#      python3 tools/build-standalone-configs.py
#
#  Drop this file into /config/esphome/. No subfolder needed, it is complete.
#
#  Required entries in /config/esphome/secrets.yaml:
#      wifi_ssid, wifi_password, api_encryption_key, ota_password
# =============================================================================

substitutions:
  device_name: esp-ac-{slug}
  room: "{room}"

"""


def main() -> None:
    TARGET.mkdir(exist_ok=True)
    base = BASE.read_text(encoding="utf-8")
    # Drop the package's own header comment; the per-room header replaces it.
    body = base[base.index("esphome:"):]

    for slug, room in ROOMS:
        path = TARGET / f"esp-ac-{slug}.yaml"
        path.write_text(HEADER.format(room=room, slug=slug) + body, encoding="utf-8")
        print(f"  {path.relative_to(ROOT)}")
    print(f"{len(ROOMS)} file(s) written.")


if __name__ == "__main__":
    main()
