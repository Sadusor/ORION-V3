"""BROWSER TESTS (optional; needs `pip install playwright` + `playwright install chromium`). Renders the REAL pages in Chromium.
 - demo.html (mock): every state / verdict / approval / stop / notice, desktop + phone.
 - index.html (live) against the fake ORION over HTTP: pairing, automatic updates, approval, reject, stop, offline, malformed, reconnect."""
import pathlib, sys, time, json, os, shutil
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
try:
    from playwright.sync_api import sync_playwright
except Exception:
    print("SKIPPED: playwright not installed (pip install playwright && playwright install chromium)"); sys.exit(0)
from fake_orion import FakeOrion, SCRIPT
ROOT = HERE.parent.parent
SHOTS = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
if SHOTS: SHOTS.mkdir(parents=True, exist_ok=True)
fails = 0; errs = []
def ok(c, m):
    global fails; fails += (not c); print(("  ok   " if c else "  FAIL ") + m)
def txt(pg, sel): return pg.inner_text(sel).strip()
def shot(pg, name):
    if SHOTS: pg.screenshot(path=str(SHOTS / (name + ".png")))
def newpage(b, w, h, mobile=False):
    ctx = b.new_context(viewport={"width": w, "height": h}); pg = ctx.new_page()
    pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" and "status of 4" not in m.text and "status of 5" not in m.text and "ERR_EMPTY_RESPONSE" not in m.text and "ERR_CONNECTION" not in m.text else None)   # induced by the deliberate offline test
    return ctx, pg
def settle(pg, want, ms=6000):
    try: pg.wait_for_function("w=>document.getElementById('stl').innerText.trim()===w", arg=want, timeout=ms); return True
    except Exception: return False
def demo(pg, s): pg.select_option("#demosel", s); pg.wait_for_timeout(250)
EXPECT = {"idle": "IDLE", "drafting": "THINKING LOCALLY", "verifying": "VERIFYING", "preparing": "PREPARING ACTION", "acting": "ACTING", "acting_powershell": "ACTING", "pass": "PASS",
          "approval": "APPROVAL NEEDED", "blocked_preflight": "BLOCKED", "failed_verification": "FAILED VERIFICATION", "capability_blocked": "BLOCKED", "run_failed": "FAILED", "stopped": "STOPPED",
          "brain_error": "ERROR", "reviewers_running": "CONSULTING SPECIALIST", "stale": "STALE DATA", "reconnecting": "RECONNECTING", "offline": "DISCONNECTED", "unpaired": "DISCONNECTED", "backend_error": "BACKEND ERROR"}
print("browser")
with sync_playwright() as p:
    exe = os.environ.get("ORION_CHROMIUM") or shutil.which("chromium") or shutil.which("google-chrome")
    b = p.chromium.launch(executable_path=exe, args=["--no-sandbox"] if exe else None)
    for name, (w, h) in {"desktop": (1400, 860), "phone": (390, 800)}.items():
        print(f"\n== demo.html · {name} ==")
        ctx, pg = newpage(b, w, h); pg.goto(os.environ.get("ORION_DEMO_URL") or ("file://" + str(ROOT / "demo.html"))); pg.wait_for_timeout(700)
        ok(pg.is_visible("#demo") and "DEMO / MOCK BACKEND" in txt(pg, "#demo"), "visible banner: DEMO / MOCK BACKEND"); ok(pg.title().startswith("[DEMO"), "tab title is marked [DEMO / MOCK]")
        for st, want in EXPECT.items():
            demo(pg, st); got = txt(pg, "#stl"); ok(got == want, f"state {st:20s} -> {got}")
        demo(pg, "pass"); ok(pg.is_visible(".chipv.exec") and "EXECUTION · completed" in txt(pg, ".chipv.exec") and "VERDICT · PASS" in txt(pg, ".chipv.pass"), "PASS card: EXECUTION completed + VERDICT PASS are separate chips")
        card = pg.inner_text(".card.main"); ok("Launch requested" in card and "not independently verified" in card and "has not read" in card, "PASS card shows launch-only proof text and says page content was not read")
        ok("Target page read / verified" in card and "not established" in card and "Browser process launched" in card, "evidence ladder: process established, page verified NOT established"); shot(pg, f"{name}-pass")
        demo(pg, "run_failed"); ok("VERDICT · FAILED" in txt(pg, ".chipv.fail") and "EXECUTION · completed" in txt(pg, ".chipv.exec"), "FAILED card: execution completed, verdict FAILED")
        demo(pg, "capability_blocked"); ok("VERDICT · BLOCKED" in txt(pg, ".chipv.warn"), "BLOCKED card: verdict BLOCKED"); shot(pg, f"{name}-blocked-cap")
        demo(pg, "stopped"); ok("EXECUTION · stopped" in txt(pg, ".chipv.exec") and "VERDICT · none" in pg.inner_text(".vrow"), "STOPPED card: execution stopped, no verdict")
        demo(pg, "failed_verification"); ok("FAILED VERIFICATION" in pg.inner_text(".card.main") and "Nothing was executed" in pg.inner_text(".card.main"), "failed-verification card (distinct from BLOCKED), nothing executed"); shot(pg, f"{name}-verif-failed")
        demo(pg, "blocked_preflight"); ok("preflight" in pg.inner_text(".card.main").lower(), "blocked card names the preflight")
        # approval UX
        demo(pg, "approval"); c = pg.inner_text(".card.approval")
        for k in ["APPROVAL NEEDED", "Local Hands · PowerShell", "Target", "Why", "Command", "Checks passed", "Scope", "Approve & Run", "Reject"]: ok(k in c, f"approval card shows '{k}'")
        ok(not pg.is_visible(".card.approval details pre"), "the raw script is NOT dumped on screen by default"); pg.click(".card.approval details summary"); ok(pg.is_visible(".card.approval details pre") and "never executed" in txt(pg, ".card.approval details pre"), "technical details expand to the exact script")
        shot(pg, f"{name}-approval")
        bb = pg.locator("[data-approve]").bounding_box(); bar = pg.locator("#bar").bounding_box()
        ok(bb and bb["height"] >= 38 and bb["x"] >= 0 and bb["x"] + bb["width"] <= w and bb["y"] + bb["height"] <= bar["y"], f"Approve & Run is fully visible ABOVE the input bar, even with details expanded ({int(bb['width'])}x{int(bb['height'])})")
        top = pg.evaluate("(()=>{const e=document.querySelector('[data-approve]');const r=e.getBoundingClientRect();return document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)===e})()"); ok(top, "Approve & Run is the topmost element at its position (nothing overlaps or intercepts it)")
        pg.click("[data-approve]"); pg.wait_for_timeout(300); ok("sent to ORION" in txt(pg, "#toast"), "a real click goes through (mock records it)")
        pg.click("[data-reject]"); pg.wait_for_timeout(250); ok("You rejected this draft" in pg.inner_text(".card.main") and txt(pg, "#stl") == "IDLE" and not pg.locator("[data-approve]").count(), "Reject: nothing runs, no Approve button left, state idle")
        pg.click("[data-unreject]"); pg.wait_for_timeout(200); ok(pg.is_visible("[data-approve]"), "Review again restores the approval")
        # stop
        demo(pg, "idle"); ok(pg.is_disabled("#stopb"), "Stop is present but disabled when nothing runs")
        demo(pg, "acting"); ok(pg.is_disabled("#stopb") and "cannot stop" in (pg.get_attribute("#stopb", "title") or ""), "capability run: Stop disabled, tooltip explains why")
        demo(pg, "acting_powershell"); ok(not pg.is_disabled("#stopb"), "PowerShell run: Stop enabled"); bb = pg.locator("#stopb").bounding_box(); ok(bb and bb["y"] + bb["height"] <= h and bb["x"] + bb["width"] <= w, "Stop is on screen"); ok(pg.evaluate("(()=>{const e=document.getElementById('stopb');const r=e.getBoundingClientRect();return document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)===e})()"), "Stop is the topmost element at its position (nothing intercepts clicks)"); shot(pg, f"{name}-acting-ps")
        # notices and errors
        demo(pg, "stale"); ok(pg.is_visible(".notice") and "last known state" in txt(pg, ".notice"), "STALE notice")
        demo(pg, "offline"); ok("Disconnected" in txt(pg, ".notice"), "DISCONNECTED notice")
        demo(pg, "backend_error"); ok("unexpected" in txt(pg, ".notice").lower(), "BACKEND ERROR notice shows the reason")
        demo(pg, "unpaired"); ok(pg.is_visible("#pair.on"), "NOT PAIRED shows the pairing overlay"); demo(pg, "idle")
        # reviewers
        demo(pg, "reviewers_running"); pg.wait_for_timeout(150); demo(pg, "reviewers_partial"); c = pg.inner_text(".card.rvs")
        ok("PARTIAL" in c and "Demo: provider rate limit" in c and "Full output" in c and "not summaries" in c, "reviewers: provider, status, verbatim closing excerpt, failure shown, full output expandable")
        ok("rollback step is missing" in c, "closing excerpt contains the reviewer's actual conclusion"); ok("does not compute agreement" in c or c.count("COMPLETE") + c.count("DONE") < 2, "no fabricated agreement/debate"); shot(pg, f"{name}-reviewers")
        # voice / view pc
        ok(pg.is_disabled("#mic"), "microphone control is disabled (voice not implemented)")
        pg.click("#viewb" if name == "desktop" else "#viewb2"); pg.wait_for_timeout(300); v = pg.inner_text("#vp")
        ok("Not configured" in v and "never authorizes" in v and pg.is_disabled("#vp button.btn") and not pg.locator("#vp video, #vp img").count(), "VIEW PC: not configured, no fake feed, viewing never authorizes control"); shot(pg, f"{name}-viewpc"); pg.click("#vp [data-close]")
        # product navigation + connector/system surface
        demo(pg, "pass");
        ok(pg.locator("#product-nav [data-view]").count() == 6, "product navigation exposes Home / Work / AI / Memory / Connectors / System")
        ok(pg.locator("#lane-strip .lane").count() == 4, "four first-class lanes are visible: Personal / Project / Specialists / Background")
        pg.click('#product-nav [data-view="ai"]'); pg.wait_for_timeout(250); ok(pg.is_visible('#workspace.on') and pg.locator('.ai-slot').count()==5, 'AI surface shows five provider slots')
        pg.click('#product-nav [data-view="connectors"]'); pg.wait_for_timeout(250); ok(pg.locator('.connector-card').count() >= 8, 'Connectors surface renders replaceable connector cards')
        pg.click('#ws-close'); pg.click("#ccb"); pg.wait_for_timeout(500)
        for sid in ["project", "github", "brain", "hands", "reviewers", "providers", "memory", "runtime", "safety", "logs"]: ok(pg.locator(f'[data-id="{sid}"]').count() == 1, f"Connectors/System section: {sid}")
        hrefs = pg.eval_on_selector_all("#legacy a", "a=>a.map(x=>x.getAttribute('href'))"); ok(hrefs == [], f"no legacy Remote links in product UI: {hrefs}")
        ok(pg.is_visible("#refreshnow") and "automatic" in (pg.get_attribute("#refreshnow", "title") or ""), "Refresh exists as a debug fallback only"); shot(pg, f"{name}-connectors")
        pg.click("#ccm"); pg.wait_for_timeout(2300); m = pg.inner_text("#mut") + pg.inner_text("#msrc")
        ok("PREVIEW" in m and "unavailable" in m and "Memory candidates" in m, "Memory Universe: labelled preview; accepted/project/history sources listed as unavailable"); shot(pg, f"{name}-memory")
        ok(pg.evaluate("document.documentElement.scrollWidth") <= w + 1 and pg.evaluate("[app.scrollTop,app.scrollLeft]") == [0, 0], "no horizontal overflow and the app container never scrolls"); ctx.close()
    # ---------------- live page against the fake ORION ----------------
    print("\n== index.html (live) vs fake ORION ==")
    f = FakeOrion().start()
    for name, (w, h) in {"desktop": (1400, 860), "phone": (390, 800)}.items():
        print(f"-- live · {name}"); f.reset()
        ctx, pg = newpage(b, w, h); pg.goto(f.base + "/v3/"); pg.wait_for_timeout(900)
        ok(pg.title() == "ORION" and pg.is_hidden("#demo") and pg.evaluate("typeof MockBridge") == "undefined", "live page: not marked demo, MockBridge does not exist")
        ok(pg.is_visible("#pair.on"), "no token => pairing overlay"); pg.fill("#pcode", "000000"); pg.click("#pgo"); pg.wait_for_timeout(400); ok("Invalid pairing code" in txt(pg, "#perr"), "wrong code => ORION's error")
        pg.fill("#pcode", f.code); pg.click("#pgo"); pg.wait_for_timeout(1000); ok(not pg.is_visible("#pair.on") and "PC CONNECTED" in txt(pg, "#connT") and txt(pg, "#stl") == "IDLE", "paired => PC CONNECTED, real IDLE")
        # automatic lifecycle (no Refresh)
        pg.fill("#inp", "Open Chrome and search Google for RTX 4070 Ti SUPER price Greece"); pg.press("#inp", "Enter"); t0 = time.time(); seen = []
        while time.time() - t0 < 9:
            s = txt(pg, "#stl")
            if not seen or seen[-1] != s: seen.append(s)
            if s == "PASS": break
            pg.wait_for_timeout(150)
        rank = {"IDLE": 0, "THINKING LOCALLY": 1, "VERIFYING": 2, "PREPARING ACTION": 3, "ACTING": 4, "PASS": 5}
        ok(seen[-1] == "PASS" and all(rank[a] <= rank[c] for a, c in zip(seen, seen[1:])) and {"THINKING LOCALLY", "PASS"} <= set(seen), "UI followed the BACKEND lifecycle automatically: " + " > ".join(seen))
        log = f.log; ok([x["path"] for x in log] == ["/api/local-hand/draft"], "only POST /api/local-hand/draft was sent (no run, no extra commands)")
        pg.wait_for_timeout(500); card = pg.inner_text(".card.main"); ok("VERDICT · PASS" in card and "EXECUTION · completed" in card and "not independently verified" in card, "live PASS card: execution + verdict + launch-only proof"); shot(pg, f"live-{name}-pass")
        # approval: approve
        f.scenario = "approval"; f.timed_goal = None; settle(pg, "APPROVAL NEEDED"); ok(txt(pg, "#stl") == "APPROVAL NEEDED", "backend approval state => APPROVAL NEEDED (found automatically), got " + txt(pg, "#stl")); ok(pg.is_visible("[data-approve]"), "approval card with Approve & Run is shown")
        n = len(f.log); pg.click(".card.approval details summary"); pg.click("[data-approve]"); settle(pg, "ACTING")
        runs = [x for x in f.log[n:] if x["path"] == "/api/local-hand/run"]; ok(len(runs) == 1 and runs[0]["body"]["script"] == SCRIPT and runs[0]["body"]["publish_github"] is False, "Approve & Run sent the exact script, once")
        ok(txt(pg, "#stl") == "ACTING" and not pg.is_disabled("#stopb"), "backend now running PowerShell => ACTING, Stop enabled")
        n = len(f.log); pg.click("#stopb"); settle(pg, "IDLE"); st = [x["path"] for x in f.log[n:]]; ok(st == ["/api/local-hand/stop"], "Stop is TARGETED: only /api/local-hand/stop was sent")
        # approval: reject
        f.scenario = "approval"; settle(pg, "APPROVAL NEEDED"); n = len(f.log); pg.click("[data-reject]"); pg.wait_for_timeout(500); ok(len(f.log) == n and txt(pg, "#stl") == "IDLE", "Reject sends NOTHING to ORION")
        # failures
        thr = "Object.assign(ORION_BRIDGE._config,{staleAfterMs:150,reconnectingAfterMs:1200,offlineAfterMs:2600,idleMs:200,activeMs:200})"; pg.evaluate(thr)
        f.scenario = "idle"; f.mode = "html"; pg.wait_for_timeout(1200); ok(txt(pg, "#stl") == "BACKEND ERROR" and "Unexpected" in txt(pg, ".notice"), "malformed backend body => BACKEND ERROR, UI alive"); shot(pg, f"live-{name}-backend-error")
        f.mode = "drop"; seq = []; t0 = time.time()
        while time.time() - t0 < 6:
            s = txt(pg, "#stl")
            if not seq or seq[-1] != s: seq.append(s)
            pg.wait_for_timeout(120)
        ok(any(x in seq for x in ["STALE DATA", "RECONNECTING"]) and seq[-1] == "DISCONNECTED", "dropped connection => " + " > ".join(seq)); shot(pg, f"live-{name}-offline")
        ok(pg.evaluate("typeof MockBridge") == "undefined" and "last" in txt(pg, ".notice").lower() or "Disconnected" in txt(pg, ".notice"), "offline: explicit notice, no fallback to mock data")
        f.mode = "ok"; pg.wait_for_function("document.getElementById('connT').innerText.includes('PC CONNECTED')", timeout=6000); ok("PC CONNECTED" in txt(pg, "#connT") and txt(pg, "#stl") in ("IDLE", "APPROVAL NEEDED"), "reconnect: recovered automatically (no Refresh pressed)")
        r = pg.request.get(f.base + "/v3/demo.html"); ok(r.status == 404, "live server refuses demo.html"); ctx.close()
    f.stop(); b.close()
ok(not errs, "no console / page errors" + ("" if not errs else ": " + "; ".join(errs[:4])))
print(f"browser: {'ALL PASS' if not fails else str(fails) + ' FAILED'}"); sys.exit(1 if fails else 0)
