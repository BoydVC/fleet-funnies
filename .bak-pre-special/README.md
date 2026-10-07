# Fleet Funnies

**A daily comic strip starring Boyd's Grok Bots.** It's generated automatically from Bot Island's fleet data and drawn in hand-made SVG.
Every gag is grounded in a real logged event, and the source event is printed in small text under each panel.

- **Live:** http://127.0.0.1:4142/ (`./run.sh` starts or restarts it in the background)
- **Offline:** `dist/fleet-funnies-snapshot.html`, one self-contained file with fonts and every strip inlined
- **Print the funnies:** `dist/fleet-funnies-print.pdf`, letter size, 5 pages (the Sunday special, then 3 dailies per page)
- **PNGs:** `dist/png/<strip>.png` (2×) and `dist/png/panels/<strip>-pN.png` for single panels
- **Screenshots:** `screenshots/*.png` (1440×900, plus one long comics-page capture)

![Comics page](screenshots/01-comics-page.png)

## The strips (11)
| Date | Title | Beats the generator picked | PNG |
|---|---|---|---|
| Thursday, August 20, 2026 | **Inbox Zero (Not Today)** | day-one, msg-storm, boyd-visits, busiest | `dist/png/daily-2026-08-20.png` |
| Tuesday, September 8, 2026 | **Passing the Torch** | pam-scan, handoff-jim, boyd-visits, night | `dist/png/daily-2026-09-08.png` |
| Wednesday, September 9, 2026 | **The New Kid at the Post Office** | handoff-brief, tutor-screens, paused-copies, msg-storm | `dist/png/daily-2026-09-09.png` |
| Friday, September 11, 2026 | **Brief Sleeps In** | long-run, brief-overslept, msg-storm | `dist/png/daily-2026-09-11.png` |
| Sunday, September 13, 2026 | **Fifth Pick, Take Two** | long-run, simmons-twice, night | `dist/png/daily-2026-09-13.png` |
| Monday, September 14, 2026 | **Stop the Presses (Both of Them)** | two-presses, eggbot-checkup, oscar-rush | `dist/png/daily-2026-09-14.png` |
| Tuesday, September 15, 2026 | **Passing Notes** | brief-overslept, oscar-rush, tutor-notes | `dist/png/daily-2026-09-15.png` |
| Wednesday, September 16, 2026 | **To Be Continued...** | two-presses, long-run, logs-end | `dist/png/daily-2026-09-16.png` |
| Tuesday, October 6, 2026 | **The PDF-Only Era** | printer-offline, dawn-patrol, jim-night, night | `dist/png/daily-2026-10-06.png` |
| Wednesday, October 7, 2026 | **TokenMax Build Night** | printer-back, tokenmax-build | `dist/png/daily-2026-10-07.png` |
| Sunday Special (Oct 7) | **TokenMax Build Night: The Sunday Special** | TokenMax Hub + usage.json | `dist/png/sunday-build-night.png` |

Best single panel: `dist/png/panels/daily-2026-09-14-p2.png`. The archive Family Times meets the live Family Times at the same press ("Wait... aren't you ME?").

## How it works
```
build/beats.py         reads Bot Island data (read-only), indexes it by ET day, and runs the beat detectors
build/art.py           SVG bots (Bot Island's body shapes + colors, visor faces, antenna lights), Boyd in his Ravens #8, props
build/scenes.py        Bot Island's places as panel backdrops (press, post office, bank, schoolhouse, HQ, library, launch pad…), bubbles
build/compose.py       panels → 4-panel dailies (muted newsprint) and the Sunday color strip (banner + 8 panels)
build/generate.py      picks the days and beats, then writes strips/*.svg, strips/panels/*.svg and data/strips.json
build/render.py        headless Chrome: PNGs (2×) + the letter-size print PDF (dist/print.html → dist/fleet-funnies-print.pdf)
build/export_static.py → dist/fleet-funnies-snapshot.html
web/                   comics-page viewer (index.html, style.css, app.js, fonts.js = Bangers + Comic Neue, embedded)
server.py / run.sh     127.0.0.1:4142 (serves web/, /data, /dist, /strips, /api/health)
tests/smoke_test.py    grounding + rendering checks (see below)
```
Rebuild everything with `./build.sh`, then `./screenshot.sh` and `python3 tests/smoke_test.py`.

**Picking the funniest true beats.** Each detector looks for a pattern in one day's real events and returns scored panels. These are the beats:
- two Family Times bots doing the same job at the same press
- Brief with no run on a weekday it's scheduled
- Michael's two paused routine copies
- the day Jim and Brief took over Michael's routines
- Oscar's money checks firing minutes apart
- bot-to-bot message storms
- the tutors messaging each other and tying on screen sessions
- the printer offline (PDF-only streaks) and back again
- Path's HSPT sheets and Pods' feed around 6:50 AM
- Jim's Simmons pick running twice on Sunday
- Dr. EggBot's checkup and Ryan's digest
- Boyd's check-ins
- the day the local logs end
- TokenMax burning fuel before the reset

For each day the generator fills 4 panels greedily by score, without letting the same bot or topic appear twice. A gag that already ran on an earlier day gets a score penalty and a different line, so repeats read as "again". Days are picked so every signature gag shows up at least once, then filled with the funniest remaining days. Today is always included.

**Sunday special.** This summarizes tonight's build with the TokenMax Hub's `/api/hub` (read-only GET; a copy is saved to `data/hub-snapshot.json`) and `../usage.json`. It includes project first-file times, files, lines of code, screenshots and live ports, plus the fuel gauge at 3:22 PM and 4:40 PM.

**Viewer.** It has a comics-page view (Sunday first, then dailies newest first) and a one-strip view with ◀ ▶ (or ← →). The archive chips jump to any strip. ⬇ PNG renders the strip to a 2× PNG in the browser. 🖨️ opens the print PDF; the offline snapshot prints the page with letter-size print CSS instead. Deep links: `/#daily-2026-09-11`, `/?view=single#sunday-build-night`.

## Grounding rules
- Speech-bubble lines are comic dialogue. Everything they assert (times, counts, who ran what) comes from the data shown in the source line.
- No message content, prompts or private text is used. Bot Island only stores timestamps and senders, and only those are used here.
- The smoke test checks every clock time printed in a panel (caption, bubble or source) against a real event, a scheduled cron fire or a data timestamp for that day. It also re-derives the message, computer-use, Boyd check-in and event counts, the edition print status, the "no Brief run" claims, the hub counts and usage.json. It checks for a list of mean or crude words, and that every bot is drawn in its real Bot Island color.

## Sources (all read-only)
- `/workspace/tokenmax/bot-island/data/fleet.json`: routine runs, outputs (file writes, dated outputs), bot-to-bot messages, computer-use sessions, Boyd check-ins, newspaper edition log, tokenFuel
- `/workspace/tokenmax/bot-island/config.json`: places (`buildings`). Avatar shapes and colors come from fleet.json. The body-shape geometry is ported from Bot Island's `web/app.js`.
- Fleet Doctor findings (two bots one job, missed runs, paused copies, routines within 20 minutes) are named in source lines as they appear in Bot Island's report.
- `/workspace/tokenmax/usage.json` and `http://127.0.0.1:4646/api/hub` (TokenMax Hub)

## Caveats
- Bot Island's local logs end **Sep 16, 2026 5:30 AM ET** (box restored Oct 3). Strips after that rely on output files: the edition log, Path/Pods/Jim files and TokenMax's files.
- Times marked ≈ are Bot Island's "dated output" placements (the file name has the date; the time is the bot's usual time).
- The tutors' check-ins ran around 7 PM ET in the logs even though their cron fields read 5:45 and 6:15. The strips show the logged times.
- Hub numbers are file counts and mtimes at generation time, not effort. Re-run `./build.sh` to refresh the Sunday strip.
- Nothing was sent or printed. The PDF is a file on disk.
