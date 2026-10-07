#!/usr/bin/env bash
# 1440x900 screenshots of the viewer (live server, else the offline snapshot).
cd "$(dirname "$0")"; mkdir -p screenshots
BASE=http://127.0.0.1:4142/
curl -sf -o /dev/null "$BASE" || BASE="file://$PWD/dist/fleet-funnies-snapshot.html"
shot(){ P=$(mktemp -d /tmp/ff-shot.XXXX); google-chrome --headless=new --no-sandbox --disable-gpu --hide-scrollbars --user-data-dir=$P \
  --window-size=1440,${3:-900} --virtual-time-budget=6000 --screenshot="$PWD/screenshots/$1.png" "$BASE$2" >/dev/null 2>&1; rm -rf $P; echo "screenshots/$1.png"; }
shot 01-comics-page ""
shot 02-today-build-night "?view=single#daily-2026-10-07"
shot 03-sunday-special "?view=single#sunday-build-night"
shot 04-brief-sleeps-in "?view=single#daily-2026-09-11"
shot 05-stop-the-presses "?view=single#daily-2026-09-14"
shot 06-pdf-only-era "?view=single#daily-2026-10-06"
shot 07-comics-page-long "" 2600
