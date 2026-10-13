#!/usr/bin/env python3
"""
Pre-publish checks for the whole site (run before every commit).
Usage: python3 scripts/check.py [blog/<slug>.html ...]
With no args it checks every HTML file. Exit code 1 on any failure.
"""
import json, re, sys, pathlib, html as h

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://www.brandexpro.in"

# Named creators / public figures must never appear (descriptive style names only).
BANNED = ["hormozi","gary vee","vaynerchuk","mrbeast","mr beast","iman gadzhi","ali abdaal","dan koe","grant cardone",
          "huberman","casey neistat","emma chamberlain","logan paul","khaby","charli d","addison rae","hasan",
          "cody ko","matt d'avella","mkbhd","marques","peter mckinnon","chris do","codie sanchez","leila hormozi",
          "steven bartlett","diary of a ceo","tony robbins","mel robbins","jay shetty","lewis howes","tai lopez",
          "andrew tate","joe rogan","lex fridman","justin welsh","sahil bloom","naval","alex becker","ryan trahan"]
# Phrases that conflict with the positioning (overseas clients only, pilot is paid).
BANNED_PHRASES = ["inspired by","brandexvideo","overseas clients","usa clients","free shoot","free session","free trial","free consultation"]
# Brandex never publishes prices: block rupee amounts and per-video/per-month price patterns.
PRICE_RE = re.compile(r"(₹|\brs\.?\s*\d|\binr\s*\d|\b\d[\d,]*\s*(?:k|lakh|lakhs)\b\s*(?:per|/|a)\s*(?:month|video|shoot|session)|\$\s?\d)", re.I)

def check_file(p):
    errs = []
    s = p.read_text(encoding="utf-8"); low = s.lower()
    rel = p.relative_to(ROOT).as_posix()
    # title
    m = re.search(r"<title>(.*?)</title>", s, re.S)
    if not m: errs.append("no <title>")
    else:
        t = h.unescape(m.group(1)).strip()
        if len(t) > 65: errs.append(f"title {len(t)} chars > 65")
        if "brandex" not in t.lower(): errs.append("title missing brand")
    # description
    m = re.search(r'<meta name="description" content="(.*?)">', s, re.S)
    if not m: errs.append("no meta description")
    else:
        L = len(h.unescape(m.group(1)))
        if not (90 <= L <= 300): errs.append(f"description length {L} (want 90-300)")
    # canonical must match path
    m = re.search(r'<link rel="canonical" href="(.*?)">', s)
    if not m: errs.append("no canonical")
    else:
        want = BASE + "/" + rel
        want = re.sub(r"index\.html$", "", want); want = re.sub(r"\.html$", "", want)
        if m.group(1) != want: errs.append(f"canonical {m.group(1)} != {want}")
    # JSON-LD parses
    for blk in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        try: json.loads(blk)
        except Exception as e: errs.append(f"JSON-LD invalid: {e}")
    if 'application/ld+json' not in s: errs.append("no JSON-LD")
    # exactly one h1
    n = len(re.findall(r"<h1[ >]", s))
    if n != 1: errs.append(f"{n} <h1> tags")
    # blog posts: FAQ + CTA + author present, no empty paragraphs
    if rel.startswith("blog/") and rel != "blog/index.html":
        for need in ['class="faq"', 'class="bcta"', 'class="author"', 'class="lead"', 'class="bmeta"']:
            if need not in s: errs.append(f"missing {need}")
        words = len(re.sub(r"<[^>]+>", " ", s[s.find("<main"):s.find("</main>")]).split())
        if words < 750: errs.append(f"only {words} words in article (min 750)")
    # banned names / phrases
    for b in BANNED:
        if b in low: errs.append(f"named creator: '{b}'")
    for b in BANNED_PHRASES:
        if b in low: errs.append(f"banned phrase: '{b}'")
    body_txt = re.sub(r"<script.*?</script>", "", s, flags=re.S)
    for mm in PRICE_RE.finditer(body_txt): errs.append(f"price mention: '{mm.group(0)}'")
    # internal links resolve
    for href in set(re.findall(r'href="(/[^"#?]*)', s)):
        if href.startswith("/img/"): continue
        path = href.rstrip("/")
        cands = [ROOT / (path.lstrip("/") + ".html"), ROOT / path.lstrip("/") / "index.html", ROOT / path.lstrip("/")]
        if href == "/": cands = [ROOT / "index.html"]
        if not any(c.exists() for c in cands): errs.append(f"broken internal link {href}")
    # unbalanced basic tags
    for tag in ["div","p","table","ul","ol","details","article","main","section"]:
        o = len(re.findall(rf"<{tag}[ >]", s)); c = len(re.findall(rf"</{tag}>", s))
        if o != c: errs.append(f"<{tag}> open {o} != close {c}")
    return errs

def check_site():
    errs = []
    sm = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    locs = re.findall(r"<loc>(.*?)</loc>", sm)
    if len(locs) != len(set(locs)): errs.append("sitemap has duplicate <loc>")
    for loc in locs:
        rel = loc.replace(BASE, "").strip("/")
        cands = [ROOT / "index.html"] if rel == "" else [ROOT / (rel + ".html"), ROOT / rel / "index.html"]
        if not any(c.exists() for c in cands): errs.append(f"sitemap points to missing page {loc}")
    posts = [p for p in (ROOT / "blog").glob("*.html") if p.name != "index.html"]
    idx = (ROOT / "blog" / "index.html").read_text(encoding="utf-8")
    ll = (ROOT / "llms.txt").read_text(encoding="utf-8")
    for p in posts:
        u = f"{BASE}/blog/{p.stem}"
        if u not in locs: errs.append(f"{p.name} not in sitemap")
        if f'href="/blog/{p.stem}"' not in idx: errs.append(f"{p.name} has no card on blog/index.html")
        if f"]({u})" not in ll: errs.append(f"{p.name} not in llms.txt")
        if idx.count(f'href="/blog/{p.stem}" class="post"') > 1: errs.append(f"{p.name} duplicated on blog index")
    return errs

if __name__ == "__main__":
    files = [pathlib.Path(a) for a in sys.argv[1:]] or sorted(ROOT.rglob("*.html"))
    bad = 0
    for p in files:
        p = p if p.is_absolute() else ROOT / p
        for e in check_file(p):
            print(f"FAIL {p.relative_to(ROOT)}: {e}"); bad += 1
    for e in check_site():
        print(f"FAIL site: {e}"); bad += 1
    print("ALL CHECKS PASSED" if not bad else f"{bad} problem(s)")
    sys.exit(1 if bad else 0)
