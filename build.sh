#!/usr/bin/env bash
# Full rebuild: strips (SVG+JSON) → PNGs + print PDF → offline snapshot.
set -e
cd "$(dirname "$0")"
python3 build/generate.py
python3 build/render.py
python3 build/export_static.py
