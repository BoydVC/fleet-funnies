#!/usr/bin/env python3
"""Fleet Funnies smoke test.
Grounding: every clock time printed in a panel (caption or source line) must match a real event, schedule or
data timestamp for that strip's day, and the counts quoted in sources are re-derived from Bot Island's data.
Also: strip counts, clean humor, avatar colors, server on :4142, PNGs, letter-size PDF, offline snapshot, headless render + PNG export."""
import json, os, re, sys, glob, shutil, subprocess, tempfile, urllib.request, collections, datetime as dt
from zoneinfo import ZoneInfo
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'build'))
from beats import Fleet, et, ET
from art import COLORS

fails, passes = [], 0
def check(ok, msg):
    global passes
    if ok: passes += 1
    else: fails.append(msg); print('FAIL', msg)

D = json.load(open(os.path.join(ROOT, 'data', 'strips.json'), encoding='utf-8'))
F = Fleet()
hub = json.load(open(os.path.join(ROOT, 'data', 'hub-snapshot.json'), encoding='utf-8'))
usage = json.load(open('/workspace/tokenmax/usage.json', encoding='utf-8'))
S = D['strips']
dailies = [s for s in S if s['kind'] == 'daily']; sundays = [s for s in S if s['kind'] == 'sunday']
today = dt.datetime.now(ET).date().isoformat()

# --- counts
check(len(dailies) >= 7, f'at least 7 daily strips ({len(dailies)})')
check(len({s['day'] for s in dailies}) == len(dailies), 'one strip per day')
check(all(s['day'] in F.days for s in dailies), 'every strip is a real logged day')
tb = [s for s in dailies if s['day'] == today]
check(len(tb) == 1 and tb[0]['title'] == 'TokenMax Build Night', "today's strip is 'TokenMax Build Night'")
check(len(sundays) == 1 and len(sundays[0]['panels']) >= 6, 'one Sunday strip with 6+ panels')
for s in dailies:
    check(len(s['panels']) == 4, f'{s["id"]}: 4 panels')

# --- allowed times per day (events, schedules, data timestamps)
def cron_times(cron, day):
    m, h, _, _, dow = cron.split()
    d = dt.date.fromisoformat(day); wd = (d.weekday() + 1) % 7
    ok = dow == '*' or any((lambda a, b: int(a) <= wd <= int(b))(*(x.split('-') + [x])[:2]) if '-' in x else int(x) == wd for x in dow.split(','))
    return {f'{int(hh) % 12 or 12}:{int(m):02d} {"AM" if int(hh) < 12 else "PM"}' for hh in h.split(',')} if ok else set()
def fmt(t): return t.strftime('%-I:%M %p')
TIME_RE = re.compile(r'(\d{1,2}:\d{2}) ?(AM|PM)')
allowed = collections.defaultdict(set)
for day, rs in F.runs.items():
    for r in rs:
        allowed[day] |= {fmt(r['start'])} | ({fmt(r['end'])} if r['end'] else set())
for day, os_ in F.outputs.items():
    for o in os_: allowed[day].add(fmt(o['t']))
for day, ms in F.msgs.items():
    for t, _, _ in ms: allowed[day].add(fmt(t))
for day, (t, _, _) in F.last_event.items(): allowed[day].add(fmt(t))
for e in F.d['events']:
    t = et(e['ts']); allowed[t.date().isoformat()].add(fmt(t))
for b in F.d['bots']:
    for r in b['routines']:
        for day in F.days: allowed[day] |= cron_times(r['cron'], day)
glob_ok = {fmt(F.audit_end), fmt(et(F.d['tokenFuel']['checkedAt'])), fmt(dt.datetime.fromisoformat(usage['checked_at']).astimezone(ET)),
           fmt(et(usage.get('reset_at') or usage['reset_date'] + 'T00:00:00Z'))}
glob_ok |= {fmt(dt.datetime.fromisoformat(p['firstMtime'])) for p in hub['projects'] if p.get('firstMtime')}
glob_ok |= {f'{a} {b}' for a, b in TIME_RE.findall(F.cfg.get('_artifactsIgnoreBefore_note', ''))}   # the Oct 3 box restore
TIME = TIME_RE
n_times = 0
for s in S:
    day = s['day']
    for i, p in enumerate(s['panels']):
        check(len(p['source']) > 30, f'{s["id"]} p{i + 1}: has a source line')
        texts = [p['caption'] or '', p['source']] + [b['text'] for b in p['say']]
        for txt in texts:
            for m in TIME.finditer(txt):
                n_times += 1
                tm = f'{m.group(1)} {m.group(2)}'; d = day
                pre = re.search(r'(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) (\w{3}) (\d{1,2}) $', txt[:m.start()])
                if pre:  # explicitly dated reference to another day, e.g. "Tue Sep 8 8:49 AM"
                    d = dt.datetime.strptime(f'2026 {pre.group(1)} {pre.group(2)}', '%Y %b %d').date().isoformat()
                check(tm in allowed[d] or tm in glob_ok, f'{s["id"]} p{i + 1}: time {tm} not a real event/schedule on {d}')
print(f'clock times checked against data: {n_times}')

# --- counts quoted in sources, re-derived
for s in S:
    day = s['day']
    for i, p in enumerate(s['panels']):
        src = p['source']; tag = f'{s["id"]} p{i + 1}'
        m = re.search(r'(\d+) bot-to-bot messages on', src)
        if m: check(int(m.group(1)) == len(F.msgs.get(day, [])), f'{tag}: message count')
        for who, n in re.findall(r'(Vic Tutor|Char Tutor) (\d+)', src):
            if 'computer-use' in src: check(F.cu[day].get(who, 0) == int(n), f'{tag}: computer-use count {who}')
        m = re.search(r'print = (pdf-only|printed)', src)
        if m: check(F.editions[day]['print'] == m.group(1), f'{tag}: edition print status')
        if 'No run logged' in src: check(not any(r['bot'] == 'Brief' for r in F.runs.get(day, [])), f'{tag}: Brief really has no run')
        m = re.search(r'(\d+) messages from Boyd', src)
        if m: check(int(m.group(1)) == len(F.boyd.get(day, [])), f'{tag}: Boyd message count')
        m = re.search(r'(\d+) logged events', src)
        if m: check(int(m.group(1)) == F.total[day], f'{tag}: event total')
        m = re.search(r'used_pct (\d+)', src)
        if m: check(int(m.group(1)) == usage['used_pct'], f'{tag}: usage.json used_pct')
        for name, files, loc, shots in re.findall(r'"([\w-]+)" first file [^;]+; (\d+) files, ([\d,]+) lines of code, (\d+) screenshots', src):
            hp = next(x for x in hub['projects'] if x['name'] == name)
            check((hp['counts']['files'], hp['counts']['loc'], hp['counts']['screenshots']) == (int(files), int(loc.replace(',', '')), int(shots)), f'{tag}: hub counts for {name}')
        for bot, routine in re.findall(r'([A-Z][\w. ()]+?) ran "([^"]+)"', src):
            bot = bot.split(': ')[-1].strip()
            if bot in F.bots: check(any(r['bot'] == bot and r['routine'] == routine for r in F.runs.get(day, [])) or any(r['routine'] == routine for d in F.runs for r in F.runs[d] if r['bot'] == bot), f'{tag}: {bot} ran {routine}')

# --- Fleet Doctor claims quoted in sources really appear in Bot Island's Fleet Doctor report
import html as _h
doc = re.sub(r'\s+', ' ', _h.unescape(re.sub(r'<[^>]+>', ' ', open('/workspace/tokenmax/bot-island/reports/fleet-health-2026-10-07.html', encoding='utf-8').read()))).lower()
PHRASES = {'missed 2 of 4 scheduled runs': 'missed 2 of 4 scheduled runs', 'two active bots share one job': 'two active bots share one job',
           'within 20 minutes': 'within 20 minutes', 'leftover paused copies': 'leftover paused copy'}
for s_ in S:
    for p in s_['panels']:
        if 'Fleet Doctor' in p['source']:
            for k, v in PHRASES.items():
                if k in p['source'].lower(): check(v in doc, f'{s_["id"]}: Fleet Doctor phrase "{k}" is in the report')

# --- clean, warm humor
BAD = re.compile(r'\b(stupid|dumb|idiot|hate|lazy|useless|loser|shut up|damn|hell|crap|sucks?|worst|fail(ed|ure)?|broken|garbage|trash)\b', re.I)
for s in S:
    for p in s['panels']:
        for b in p['say']: check(not BAD.search(b['text']), f'{s["id"]}: clean bubble: {b["text"]}')

# --- avatars use Bot Island shapes/colors
for s in S:
    for p in s['panels']:
        for who in p['cast']:
            if who == 'Boyd': continue
            b = F.bots.get(who); check(b is not None, f'{s["id"]}: {who} is a real bot')
            if b: check(COLORS.get(b['color'], '').lower() in s['svg'].lower(), f'{s["id"]}: {who} drawn in Bot Island color {b["color"]}')

# --- files: SVG, PNG (2x), PDF, snapshot
for s in S:
    check(os.path.exists(os.path.join(ROOT, 'strips', s['id'] + '.svg')), f'{s["id"]}: SVG file')
    png = os.path.join(ROOT, 'dist', 'png', s['id'] + '.png')
    check(os.path.exists(png) and os.path.getsize(png) > 50000, f'{s["id"]}: PNG export')
    if os.path.exists(png):
        w, h = re.search(r'width="(\d+)" height="([\d.]+)"', s['svg']).groups()
        import struct; pw, ph = struct.unpack('>II', open(png, 'rb').read(24)[16:24])
        check(pw == 2 * int(w), f'{s["id"]}: PNG is 2x ({pw}px)')
    for i in range(len(s['panels'])):
        check(os.path.exists(os.path.join(ROOT, 'dist', 'png', 'panels', f'{s["id"]}-p{i + 1}.png')), f'{s["id"]}: panel {i + 1} PNG')
pdf = os.path.join(ROOT, 'dist', 'fleet-funnies-print.pdf')
info = subprocess.run(['pdfinfo', pdf], capture_output=True, text=True).stdout
check('612 x 792 pts (letter)' in info, 'PDF is letter size')
pages = int(re.search(r'Pages:\s+(\d+)', info).group(1)) if 'Pages' in info else 0
check(pages >= 1 + (len(dailies) + 2) // 3, f'PDF has all strips ({pages} pages)')
txt = subprocess.run(['pdftotext', pdf, '-'], capture_output=True, text=True).stdout
check(all(s['title'].upper() in txt.upper().replace('\n', ' ') or s['title'].split(':')[0].upper() in txt.upper() for s in S), 'PDF contains every strip title')
snap = open(os.path.join(ROOT, 'dist', 'fleet-funnies-snapshot.html'), encoding='utf-8').read()
check(not re.search(r'<(script|link|img)[^>]+(src|href)=["\'](?!#|data:)', snap), 'snapshot has no external assets')
check('window.FUNNIES = ' in snap and 'FUNNIES_FONTS' in snap, 'snapshot inlines strips + fonts')

# --- server
def get(u):
    with urllib.request.urlopen(u, timeout=6) as r: return r.status, r.read()
for path in ['', 'app.js', 'style.css', 'fonts.js', 'data/strips.json', 'dist/fleet-funnies-print.pdf', 'strips/sunday-build-night.svg', 'api/health']:
    try:
        st, body = get('http://127.0.0.1:4142/' + path); check(st == 200 and len(body) > 20, f'port 4142 serves /{path}')
    except Exception as ex: check(False, f'port 4142 serves /{path}: {ex}')

# --- headless render + in-browser PNG export
chrome = shutil.which('google-chrome')
def dom(url):
    prof = tempfile.mkdtemp(prefix='ff-smoke-')
    try:
        return subprocess.run([chrome, '--headless=new', '--no-sandbox', '--disable-gpu', f'--user-data-dir={prof}', '--window-size=1440,900',
                               '--virtual-time-budget=8000', '--dump-dom', url], capture_output=True, text=True, timeout=120).stdout
    finally: shutil.rmtree(prof, ignore_errors=True)
for label, url in [('server', 'http://127.0.0.1:4142/?selftest=png'), ('snapshot', 'file://' + os.path.join(ROOT, 'dist', 'fleet-funnies-snapshot.html') + '?selftest=png')]:
    h = re.sub(r'<script\b.*?</script>', '', dom(url), flags=re.S)
    check('data-ready="1"' in h, f'{label}: viewer rendered')
    check(len(re.findall(r'<article class="strip-card', h)) >= len(S), f'{label}: every strip on the comics page')
    check(len(re.findall(r'class="chip', h)) == len(S), f'{label}: archive navigation lists every strip')
    m = re.search(r'data-png-bytes="(\d+)"', h)
    check(m and int(m.group(1)) > 100000, f'{label}: in-browser PNG export works ({m.group(1) if m else 0} chars)')

print(f'\n{passes} checks passed, {len(fails)} failed')
print('ALL PASS' if not fails else 'FAILURES')
sys.exit(1 if fails else 0)
