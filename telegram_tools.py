#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram + Hyperliquid: powiadomienia i monitoring adresow.

Konfiguracja (kolejnosc: env > plik telegram_config.json):
  TG_BOT_TOKEN  - token bota od @BotFather
  TG_CHAT_ID    - id czatu, do ktorego wysylamy

Komendy:
  python telegram_tools.py me                      # test tokenu
  python telegram_tools.py discover                # wykryj chat_id (napisz najpierw cokolwiek do bota!)
  python telegram_tools.py send "tekst wiadomosci" # wyslij wiadomosc
  python telegram_tools.py summary                 # snapshot rynku + watchlisty
  python telegram_tools.py monitor [sekundy]       # petla alertow (domyslnie 300 s)
  python telegram_tools.py listen                  # nasluch komend pisanych do bota na Telegramie
"""
import html
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = os.path.join(BASE, "telegram_config.json")
STATE_PATH = os.path.join(BASE, "telegram_monitor_state.json")
HL_API = "https://api.hyperliquid.xyz/info"

WATCH = [
    # 12 adresow z zapytania
    "0x39475d17bcd20adc540e647dae6781b153fbf3b1",
    "0xbc76170c8a15b34941ba9e00567d7e0f11ba417c",
    "0x9a31f7aff78fd464bbceb398e11b82ba633c6525",
    "0xc1efb67e9d1e5a48297046a67bed332d0f86de54",
    "0x020ca66c30bec2c4fe3861a94e4db4a498a35872",
    "0x51a04fc0b977d4d453c60f70d43119a3023a3543",
    "0xd0584dba197cc63e5df8a7641d01bc4aa8bc5c18",
    "0xaeaab54bbf65bfd6efed7d2eb68372298e3c2416",
    "0xfe35dfb17f226a61d1f8f318990e6d27944d6002",
    "0x588432f54227364caf999a6df88dbf86a90f4772",
    "0x9321d8117e73b0c79035f0e87debcfd8dbb1d75a",
    "0xd1dd6d99c5fb5d31ff52eacce5046c7158859e85",
    # 49 adresow z leaderboardu
    "0xaa53412d2249fe47c5d2790ab5728b3c564dd265",
    "0x27398ee91642c5440ac131f40388be83407f519b",
    "0x6c93e15ae14be1ef0f07f2fc151e7c91379a09cb",
    "0x2814e4612802066a76a99e8afbcdf1ec44039b08",
    "0x2cffce91b4e0c81df18726ff66b31b2b1545e1ad",
    "0x98e8118481aa01872142a7c447dbccd0528df831",
    "0x4fdeae7a71b36f92ba55790a037b26a8f44890e1",
    "0xcf3f419d08a5bdc2c6e5fbd9ad70904c5420f95f",
    "0x36cd75f8d0dcb4574013568f7a560ee03a2fd195",
    "0x184cf6ce32208e4bb324d402fdd8f5b34c810880",
    "0xe668c4300f51344d8e6cee6294cb9cd1fb5fb5ca",
    "0x6f0306dc529cfeb8e08502e5eb7a588def9ac88d",
    "0xc86781f99078e71c2cbf9cd8b9712d52b28b6e65",
    "0xbbfd8f29f9c7f7119858d9ec7f4bb896182b7d69",
    "0xa243ecc646b1ce99c8c2810b6581cce76ec6f989",
    "0x696d1265c8fc4f14797abebfae3c43ebfa9d8e28",
    "0x38bdfed8b37b236e8446f9c05b6580439235b9f0",
    "0xc8a2bf880f9ea1e6b7d6196090d3c2d77a45c041",
    "0xa8760cb7e4bc07af8560a2115f6e1b0874ccd243",
    "0x5a98c4f011e62cf3e188e4396d18a75c19b4af12",
    "0xab04d040dec929a204298d44701476968b238b69",
    "0x12f7aea21eed5461d30212ea771c4441656b8750",
    "0xb49fa1dd045ab41250293540a271fce5a7168258",
    "0xe8190864576e868e11b67ba82c9b91b7d4de3d1c",
    "0x706d2ac4b2a7a1e89b64b014e76b5b504ee51d6f",
    "0x9661390ea53e4cc9b7e02b441897132cbc771cda",
    "0x0884051c662892bfcd8a132d1404ab8a3a409cea",
    "0x396dc3e4d1051837bb559810d2b1ea7977775899",
    "0xd580b86a5db87c623763b058f3a12853bf30acb8",
    "0xecb63caa47c7c4e77f60f1ce858cf28dc2b82b00",  # Wintermute
    "0xd93db9fc95c19c1eaab854281890e9e77b18ae3f",
    "0xd9012a0c82242b04ee09e45e98b24903f982d975",
    "0x051c2e6d49cf82ebc47f08f9b85800f94fc9693c",
    "0xe912cac1a6641004a8803687ee7699227fdb0550",
    "0xd1581ae3dc981bfb70cceace6647a1c35df09dab",
    "0x8923cdff38a43d1fd59d323c35b900047e431bac",  # Draco
    "0xbf5a73e783866d34db7d76f07fda07daf22488ba",
    "0xae78adaba70f18c15418001263504af373884520",
    "0x38f9715251bd7b9962a51b6e56b547fedb11709a",
    "0x436c9c7c0eb3611565591eedee51ad149b76b3d1",
    "0xaf0fdd39e5d92499b0ed9f68693da99c0ec1e92e",
    "0xcd2123d3f00325fa83b2743ed85844f8d4bb9826",
    "0xeb0f432beecf10dcc828fc1e36a3386caf634637",
    "0xd4a22e7318faf2c73e93eb42887a2ce64467ec1f",
    "0xc3ed57a7a8fa374af47eba5dd713bc2946f800dd",  # High-Leverage BTC Short
    "0xcf7c4feb434751146a48b895e96caeb15838f92c",  # purrmaxi
    "0x201b96073f539234033e26cbd8f1b995050d1eb0",
    "0xbf6dd537825deeec24eb456e133c91b8d014ecc0",
    "0x1bf629cd9f4dbcc9fca616ccf7a19891007f5bfa",
]

LABELS = {
    "0xecb63caa47c7c4e77f60f1ce858cf28dc2b82b00": "Wintermute",
    "0x8923cdff38a43d1fd59d323c35b900047e431bac": "Draco",
    "0xc3ed57a7a8fa374af47eba5dd713bc2946f800dd": "High-Leverage BTC Short",
    "0xcf7c4feb434751146a48b895e96caeb15838f92c": "purrmaxi",
}


def load_cfg():
    cfg = {"bot_token": "", "chat_id": None}
    if os.path.exists(CFG_PATH):
        with open(CFG_PATH, encoding="utf-8") as f:
            cfg.update(json.load(f))
    cfg["bot_token"] = os.environ.get("TG_BOT_TOKEN", cfg.get("bot_token") or "")
    env_chat = os.environ.get("TG_CHAT_ID")
    if env_chat:
        cfg["chat_id"] = env_chat
    return cfg


def save_cfg(cfg):
    with open(CFG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def post_json(url, payload):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def tg(method, token, **params):
    return post_json(f"https://api.telegram.org/bot{token}/{method}", params)


def tg_get(method, token):
    with urllib.request.urlopen(
            f"https://api.telegram.org/bot{token}/{method}", timeout=30) as r:
        return json.loads(r.read().decode())


def send_text(token, chat_id, text):
    """Wysyla tekst (HTML), dzieli na czesci po 4000 znakow."""
    for i in range(0, len(text), 4000):
        chunk = text[i:i + 4000]
        for attempt in range(3):
            try:
                res = tg("sendMessage", token, chat_id=chat_id, text=chunk,
                         parse_mode="HTML", disable_web_page_preview=True)
                if not res.get("ok"):
                    # nieprawidlowy HTML -> wyslij bez formatowania
                    tg("sendMessage", token, chat_id=chat_id, text=chunk)
                break
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    time.sleep(5)
                else:
                    raise
        time.sleep(1.1)  # limit ~30 msg/s, ale grzecznie


def hl(payload):
    return post_json(HL_API, payload)


def btc_mark():
    meta = hl({"type": "metaAndAssetCtxs"})
    universe, ctxs = meta[0]["universe"], meta[1]
    for i, u in enumerate(universe):
        if u["name"] == "BTC":
            return float(ctxs[i]["markPx"]), float(ctxs[i]["funding"])
    raise RuntimeError("brak BTC")


def fetch_positions(addr):
    st = hl({"type": "clearinghouseState", "user": addr})
    out = {}
    for p in st.get("assetPositions", []):
        pos = p["position"]
        lev = pos.get("leverage")
        if isinstance(lev, dict):
            lev = lev.get("value")
        out[pos["coin"]] = {
            "szi": float(pos["szi"]),
            "entry": float(pos.get("entryPx") or 0),
            "lev": lev,
            "liq": pos.get("liquidationPx"),
            "uPnl": float(pos.get("unrealizedPnl") or 0),
        }
    return float(st.get("marginSummary", {}).get("accountValue") or 0), out


def fmt_addr(a):
    lab = LABELS.get(a)
    short = f"{a[:6]}...{a[-4:]}"
    return f"{short} ({lab})" if lab else short


def short_addr(a):
    return LABELS.get(a) or f"{a[:6]}...{a[-4:]}"


def collect_btc():
    """(mark, funding, [(addr, btc_pos, equity)]) ze swiezych zapytan."""
    mark, funding = btc_mark()
    rows = []
    for a in WATCH:
        try:
            eq, pos = fetch_positions(a)
        except Exception as e:
            print("blad", a, e)
            continue
        if "BTC" in pos:
            rows.append((a, pos["BTC"], eq))
        time.sleep(0.1)
    return mark, funding, rows


def cache_rows(max_age):
    """Wiersze (addr, btc_pos, equity) ze stanu monitora; None gdy brak pliku lub za stary."""
    if not os.path.exists(STATE_PATH):
        return None
    try:
        if time.time() - os.path.getmtime(STATE_PATH) > max_age:
            return None
        with open(STATE_PATH, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        return None
    rows = []
    for a, v in d.items():
        if a == "_liq_ts":
            continue
        btc = v.get("pos", {}).get("BTC")
        if btc:
            rows.append((a, btc, v.get("eq", 0)))
    return rows or None


def pos_line(mark, a, p):
    s = p["szi"]
    liq = f"{float(p['liq']):,.0f}" if p["liq"] else "-"
    dist = f"{(float(p['liq'])-mark)/mark*100:+.1f}%" if p["liq"] else "-"
    return (f"{'LONG' if s>0 else 'SHORT'} {abs(s):,.2f}BTC (${abs(s)*mark/1e6:,.1f}M) "
            f"{p['lev']}x | {html.escape(short_addr(a))} | PnL {p['uPnl']:+,.0f}$ | liq {liq} ({dist})")


def aggregates(mark, rows):
    L = [r for r in rows if r[1]["szi"] > 0]
    S = [r for r in rows if r[1]["szi"] < 0]
    lb = sum(abs(r[1]["szi"]) for r in L)
    sb = sum(abs(r[1]["szi"]) for r in S)
    lp = sum(r[1]["uPnl"] for r in L)
    sp = sum(r[1]["uPnl"] for r in S)
    return L, S, lb, sb, lp, sp


def build_summary(mark, funding, rows):
    L, S, lb, sb, lp, sp = aggregates(mark, rows)
    top = sorted(rows, key=lambda r: -abs(r[1]["szi"]) * mark)
    lines = [
        "<b>Hyperliquid BTC — watchlista</b>",
        f"BTC mark: <b>${mark:,.0f}</b> | funding: {funding*100:.4f}%/h",
        "",
        f"Long:  {len(L)} poz / {lb:,.1f} BTC (${lb*mark/1e6:,.1f}M) | uPnL {lp:+,.0f}$",
        f"Short: {len(S)} poz / {sb:,.1f} BTC (${sb*mark/1e6:,.1f}M) | uPnL {sp:+,.0f}$",
        f"Netto: {lb-sb:+,.1f} BTC",
        "",
        "<b>Najwieksze pozycje BTC:</b>",
    ]
    for a, p, eq in top[:8]:
        lines.append(pos_line(mark, a, p))
    return "\n".join(lines)


def build_top(mark, rows, n=10):
    top = sorted(rows, key=lambda r: -abs(r[1]["szi"]) * mark)
    lines = [f"<b>Top {n} pozycji BTC</b> — mark ${mark:,.0f}"]
    for a, p, eq in top[:n]:
        lines.append(pos_line(mark, a, p))
    return "\n".join(lines)


def build_liq(mark, rows, n=8):
    wl = [(a, p) for a, p, eq in rows if p["liq"]]
    wl.sort(key=lambda ap: abs((float(ap[1]["liq"]) - mark) / mark))
    lines = [f"<b>Najblizej likwidacji (BTC)</b> — mark ${mark:,.0f}"]
    if not wl:
        lines.append("Brak pozycji z wyliczona likwidacja.")
    for a, p in wl[:n]:
        dist = (float(p["liq"]) - mark) / mark * 100
        lines.append(f"{'L' if p['szi']>0 else 'S'} {abs(p['szi']):,.2f}BTC {p['lev']}x | "
                     f"liq {float(p['liq']):,.0f} ({dist:+.1f}%) | {html.escape(short_addr(a))}")
    return "\n".join(lines)


def build_addr(addr):
    meta = hl({"type": "metaAndAssetCtxs"})
    marks = {u["name"]: float(c["markPx"]) for u, c in zip(meta[0]["universe"], meta[1])}
    eq, pos = fetch_positions(addr)
    lines = [f"<b>{html.escape(short_addr(addr))}</b> — equity <b>${eq:,.0f}</b>"]
    if not pos:
        lines.append("Brak otwartych pozycji.")
        return "\n".join(lines)
    items = sorted(pos.items(), key=lambda kv: -abs(kv[1]["szi"]) * marks.get(kv[0], 0))
    for coin, p in items[:15]:
        m = marks.get(coin)
        val = abs(p["szi"]) * m if m else 0
        dist = f"{(float(p['liq'])-m)/m*100:+.1f}%" if (p["liq"] and m) else "-"
        lines.append(f"{'L' if p['szi']>0 else 'S'} {coin} {abs(p['szi']):,.4g} (${val:,.0f}) "
                     f"{p['lev']}x | PnL {p['uPnl']:+,.0f}$ | liq {dist}")
    if len(items) > 15:
        lines.append(f"...+{len(items)-15} mniejszych")
    return "\n".join(lines)


HELP_TEXT = (
    "<b>Bot Hyperliquid — komendy:</b>\n"
    "/cena — cena BTC + funding (alias /btc)\n"
    "/podsumowanie — pelny snapshot watchlisty (alias /summary)\n"
    "/top — 10 najwiekszych pozycji BTC\n"
    "/likwidacje — pozycje najblizej likwidacji\n"
    "/netto — agregat long/short (alias /net)\n"
    "/adres 0x... — szczegoly konta (alias /addr)\n"
    "/help — ta pomoc\n\n"
    "/top, /likwidacje, /netto czytaja cache monitora (odswiezany co 10 min); "
    "/podsumowanie i /adres pobieraja dane na zywo."
)


def handle_command(cfg, chat, text):
    token = cfg["bot_token"]
    if str(chat) != str(cfg.get("chat_id")):
        send_text(token, chat, "Bot prywatny — brak dostepu.")
        return
    parts = text.split()
    cmd = parts[0].lower().split("@")[0]
    if cmd in ("/start", "/help", "/komendy"):
        send_text(token, chat, HELP_TEXT)
    elif cmd in ("/price", "/btc", "/cena"):
        mark, funding = btc_mark()
        send_text(token, chat, f"BTC mark: <b>${mark:,.0f}</b>\nFunding: {funding*100:.4f}%/h")
    elif cmd in ("/summary", "/podsumowanie"):
        rows = cache_rows(900)
        if rows:
            mark, funding = btc_mark()
            note = "\n\n<i>(cache monitora, mlodszy niz 15 min)</i>"
        else:
            mark, funding, rows = collect_btc()
            note = ""
        send_text(token, chat, build_summary(mark, funding, rows) + note)
    elif cmd == "/top":
        rows = cache_rows(1800)
        if rows:
            mark, funding = btc_mark()
        else:
            mark, funding, rows = collect_btc()
        send_text(token, chat, build_top(mark, rows))
    elif cmd in ("/likwidacje", "/liq"):
        rows = cache_rows(1800)
        if rows:
            mark, funding = btc_mark()
        else:
            mark, funding, rows = collect_btc()
        send_text(token, chat, build_liq(mark, rows))
    elif cmd in ("/net", "/netto", "/pnl"):
        rows = cache_rows(1800)
        if rows:
            mark, funding = btc_mark()
        else:
            mark, funding, rows = collect_btc()
        L, S, lb, sb, lp, sp = aggregates(mark, rows)
        send_text(token, chat,
                  f"<b>Agregat watchlisty</b> (BTC ${mark:,.0f})\n"
                  f"Long:  {len(L)} poz / {lb:,.1f} BTC (${lb*mark/1e6:,.1f}M) | uPnL {lp:+,.0f}$\n"
                  f"Short: {len(S)} poz / {sb:,.1f} BTC (${sb*mark/1e6:,.1f}M) | uPnL {sp:+,.0f}$\n"
                  f"Netto: {lb-sb:+,.1f} BTC")
    elif cmd in ("/addr", "/adres"):
        if len(parts) < 2:
            send_text(token, chat, "Uzycie: /adres 0x...")
        else:
            addr = parts[1].lower()
            if not addr.startswith("0x") or len(addr) != 42:
                send_text(token, chat, "To nie wyglada jak adres EVM (0x + 40 znakow hex).")
            else:
                send_text(token, chat, build_addr(addr))
    else:
        send_text(token, chat, "Nieznana komenda.\n\n" + HELP_TEXT)


def cmd_listen(cfg):
    token = cfg["bot_token"]
    offset = 0
    print("Nasluch komend aktywny.", flush=True)
    while True:
        try:
            req = urllib.request.Request(
                f"https://api.telegram.org/bot{token}/getUpdates",
                data=json.dumps({"offset": offset, "timeout": 30}).encode(),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=45) as r:
                res = json.loads(r.read().decode())
            for u in res.get("result", []):
                offset = u["update_id"] + 1
                m = u.get("message") or u.get("edited_message")
                if not m or not isinstance(m.get("text"), str):
                    continue
                chat = m["chat"]["id"]
                print(f"komenda od {chat}: {m['text']!r}", flush=True)
                try:
                    handle_command(cfg, chat, m["text"].strip())
                except Exception as e:
                    send_text(token, chat, f"Blad komendy: {e}")
        except urllib.error.HTTPError as e:
            body = e.read()[:200]
            if e.code == 409:
                print("409: inny proces czyta getUpdates (discover/listen gdzie indziej?)", body, flush=True)
                time.sleep(15)
            else:
                print("HTTP", e.code, body, flush=True)
                time.sleep(5)
        except Exception as e:
            print("blad nasluchu:", e, flush=True)
            time.sleep(5)


def tg_offset_load():
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, encoding="utf-8") as f:
                return json.load(f).get("_tg_offset", 0)
        except Exception:
            return 0
    return 0


def tg_offset_save(off):
    d = {}
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            d = {}
    d["_tg_offset"] = off
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(d, f)


def cmd_cycle(cfg):
    """Jeden cykl dla chmury (GitHub Actions): najpierw monitoring (alerty),
    potem odpowiedzi na zalegle komendy. Persystuje offset Telegrama i stan."""
    cmd_monitor(cfg, 0, once=True)
    token = cfg["bot_token"]
    offset = tg_offset_load()
    try:
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/getUpdates",
            data=json.dumps({"offset": offset, "timeout": 0}).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            res = json.loads(r.read().decode())
        for u in res.get("result", []):
            offset = u["update_id"] + 1
            m = u.get("message") or u.get("edited_message")
            if not m or not isinstance(m.get("text"), str):
                continue
            print(f"komenda: {m['text']!r}", flush=True)
            try:
                handle_command(cfg, m["chat"]["id"], m["text"].strip())
            except Exception as e:
                print("blad komendy:", e, flush=True)
    except Exception as e:
        print("blad getUpdates:", e, flush=True)
    tg_offset_save(offset)


# ---------------- komendy ----------------

def cmd_me(cfg):
    res = tg_get("getMe", cfg["bot_token"])
    print(json.dumps(res, indent=2))
    if res.get("ok"):
        b = res["result"]
        print(f"\nBot: @{b.get('username')} (id {b.get('id')})")
        print("Token poprawny.")


def cmd_discover(cfg):
    res = tg_get("getUpdates", cfg["bot_token"])
    if not res.get("ok"):
        print("Blad:", res)
        return
    chats = {}
    for u in res.get("result", []):
        for key in ("message", "channel_post", "edited_message", "my_chat_member"):
            m = u.get(key)
            if not m:
                continue
            c = m.get("chat") or {}
            if c.get("id") is not None:
                name = " ".join(x for x in [c.get("first_name"), c.get("title")] if x) or c.get("username") or ""
                chats[c["id"]] = name.strip()
    if not chats:
        print("Nikt jeszcze nie napisal do bota. Otworz Telegram, znajdz swojego bota")
        print("(username z getMe) i wyslij mu /start , potem uruchom discover ponownie.")
        return
    for cid, name in chats.items():
        print(f"chat_id: {cid}   {name}")
    if len(chats) == 1 and not cfg.get("chat_id"):
        cfg["chat_id"] = next(iter(chats))
        save_cfg(cfg)
        print(f"\nZapisalem chat_id={cfg['chat_id']} do {os.path.basename(CFG_PATH)}")


def cmd_send(cfg, text):
    if not cfg.get("chat_id"):
        sys.exit("Brak chat_id - uruchom najpierw 'discover' lub ustaw TG_CHAT_ID.")
    send_text(cfg["bot_token"], cfg["chat_id"], html.escape(text))
    print("wyslano")


def cmd_summary(cfg):
    mark, funding, rows = collect_btc()
    txt = build_summary(mark, funding, rows)
    send_text(cfg["bot_token"], cfg["chat_id"], txt)
    print(txt)


SIZE_CHANGE_ALERT = 0.05   # 5% zmiana wielkosci pozycji
LIQ_WARN = 0.03            # alerty gdy likwidacja BTC blizej niz 3%
LIQ_COOLDOWN = 6 * 3600    # ostrzezenie likwidacji dla konta max raz na 6 h


def snapshot():
    mark, funding = btc_mark()
    data = {}
    for a in WATCH:
        try:
            eq, pos = fetch_positions(a)
        except Exception as e:
            print("blad", a, e)
            continue
        data[a] = {"eq": eq, "pos": pos}
        time.sleep(0.1)
    return mark, funding, data


def cmd_monitor(cfg, poll_sec, once=False):
    prev = None
    liq_ts = {}
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, encoding="utf-8") as f:
            saved = json.load(f)
        liq_ts = saved.pop("_liq_ts", {})
        prev = saved
    print(f"Start monitoringu, co {poll_sec}s; watchlista: {len(WATCH)} adresow")
    while True:
        try:
            mark, funding, data = snapshot()
            alerts = []
            for a, cur in data.items():
                was = (prev or {}).get(a, {}).get("pos", {})
                for coin, p in cur["pos"].items():
                    old = was.get(coin)
                    side = "LONG" if p["szi"] > 0 else "SHORT"
                    if old is None:
                        alerts.append(f"NOWA {side} {coin} {abs(p['szi']):,.4g} @ {p['entry']:,.4g} "
                                      f"({p['lev']}x) — {short_addr(a)}")
                    elif old["szi"] != 0 and abs(p["szi"] - old["szi"]) / abs(old["szi"]) >= SIZE_CHANGE_ALERT:
                        alerts.append(f"ZMIANA {side} {coin}: {old['szi']:,.4g} -> {p['szi']:,.4g} "
                                      f"({(p['szi']-old['szi'])/abs(old['szi'])*100:+.0f}%) — {short_addr(a)}")
                for coin, old in was.items():
                    if coin not in cur["pos"]:
                        alerts.append(f"ZAMKNIETA {coin} (bylo {old['szi']:,.4g}) — {short_addr(a)}")
                # ostrzezenia o likwidacji BTC (max raz na LIQ_COOLDOWN dla konta)
                p = cur["pos"].get("BTC")
                if p and p["liq"]:
                    dist = (float(p["liq"]) - mark) / mark
                    if abs(dist) < LIQ_WARN and time.time() - liq_ts.get(a, 0) >= LIQ_COOLDOWN:
                        liq_ts[a] = time.time()
                        alerts.append(f"⚠️ LIKW BLISKO: {'LONG' if p['szi']>0 else 'SHORT'} "
                                      f"{abs(p['szi']):,.2f}BTC, likw {float(p['liq']):,.0f} "
                                      f"({dist*100:+.1f}%) — {short_addr(a)}")
            if prev is None:
                print("Pierwszy przebieg — zapisuje stan bazowy (bez alertow)")
            elif alerts:
                msg = (f"<b>Alerty Hyperliquid</b> (BTC ${mark:,.0f})\n\n"
                       + "\n".join(html.escape(x) for x in alerts[:40]))
                send_text(cfg["bot_token"], cfg["chat_id"], msg)
                print(f"[{time.strftime('%H:%M:%S')}] wyslano {len(alerts)} alertow")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] OK, brak zmian (BTC ${mark:,.0f})")
            prev = {a: {"eq": v["eq"], "pos": v["pos"]} for a, v in data.items()}
            with open(STATE_PATH, "w", encoding="utf-8") as f:
                json.dump({**prev, "_liq_ts": liq_ts}, f)
            if once:
                print("cykl jednokrotny zakonczony", flush=True)
                return
        except KeyboardInterrupt:
            print("stop")
            return
        except Exception as e:
            print("blad cyklu:", e)
        time.sleep(poll_sec)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd, cfg = sys.argv[1], load_cfg()
    if cmd != "me" and not cfg["bot_token"]:
        sys.exit("Brak tokenu. Ustaw TG_BOT_TOKEN lub bot_token w telegram_config.json")
    if cmd == "me":
        cmd_me(cfg)
    elif cmd == "discover":
        cmd_discover(cfg)
    elif cmd == "send":
        cmd_send(cfg, " ".join(sys.argv[2:]))
    elif cmd == "summary":
        cmd_summary(cfg)
    elif cmd == "monitor":
        cmd_monitor(cfg, int(sys.argv[2]) if len(sys.argv) > 2 else 300)
    elif cmd == "listen":
        cmd_listen(cfg)
    elif cmd == "cycle":
        cmd_cycle(cfg)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
