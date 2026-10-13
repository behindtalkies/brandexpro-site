#!/usr/bin/env python3
"""
Build a Brandex (brandexpro.in) blog post from a JSON spec and wire it into the site.

Usage:  python3 scripts/new_post.py content/drafts/<slug>.json

Spec (JSON) fields:
  slug          "personal-branding-for-doctors-chennai"   (lowercase, hyphens; becomes /blog/<slug>)
  seo_title     "<=58 chars>"                              (" | Brandex" is appended; total must be <=65)
  h1            "Personal Branding for Doctors in Chennai: What Actually Works"
  description   "120-160 chars, answer-first, contains the keyword"
  category      "Doctors" | "Entrepreneurs" | "Professionals" | "LinkedIn" | "Video Strategy" | "Behind the Scenes" | "Guides" | "Chennai"
  date          "2026-10-15"                              (ISO)
  read_min      6
  lead          "HTML (no <p>) for the answer-first lead; may contain <strong>"
  body          "HTML: <h2>, <h3>, <p>, <ul>, <ol>, <table>, <div class=\"callout\">..."
  faqs          [{"q": "...", "a": "..."}, ...]            (4-6, plain text)
  card_blurb    "1-2 sentence blurb for the blog index card (plain text)"
  llms_blurb    "One-line summary for llms.txt (plain text)"

Does: writes blog/<slug>.html (same CSS/nav/footer as the home page + article styles, with
BlogPosting + BreadcrumbList + FAQPage schema), inserts a card at the top of blog/index.html,
adds the URL to sitemap.xml, appends a line to llms.txt. Idempotent per slug.
"""
import json, re, sys, html, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://www.brandexpro.in"
HOME = ROOT / "index.html"

ARTICLE_CSS = """
.bwrap{max-width:760px;margin:0 auto;padding:7.5rem 5% 4rem}
.eyebrow{display:inline-block;font-family:var(--body);font-size:.7rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--gold);margin-bottom:1rem}
.bwrap h1{font-family:var(--heading);font-weight:800;font-size:clamp(1.9rem,4.2vw,2.8rem);line-height:1.15;letter-spacing:-.02em;color:var(--white);margin-bottom:1.1rem}
.bmeta{display:flex;flex-wrap:wrap;gap:1rem 1.5rem;font-size:.82rem;color:var(--muted);padding-bottom:1.5rem;border-bottom:1px solid var(--border);margin-bottom:2rem}
.lead{font-size:1.12rem;line-height:1.75;color:var(--off-white);background:var(--gold-faint);border-left:3px solid var(--gold);border-radius:0 var(--r) var(--r) 0;padding:1.25rem 1.5rem;margin:0 0 2rem}
.bwrap h2{font-family:var(--heading);font-weight:700;font-size:1.45rem;line-height:1.3;color:var(--white);margin:2.5rem 0 .9rem}
.bwrap h3{font-family:var(--heading);font-weight:700;font-size:1.08rem;color:var(--gold-lt);margin:1.75rem 0 .6rem}
.bwrap p{font-size:1.02rem;line-height:1.8;color:var(--gray-lt);margin:0 0 1.1rem}
.bwrap a{color:var(--gold-lt);text-decoration:underline;text-underline-offset:3px}
.bwrap ul,.bwrap ol{margin:0 0 1.25rem 1.3rem;color:var(--gray-lt);line-height:1.75}
.bwrap li{margin-bottom:.45rem}
.bwrap table{width:100%;border-collapse:collapse;margin:1.5rem 0;font-size:.93rem;background:var(--card);border:1px solid var(--border);border-radius:var(--r);overflow:hidden}
.bwrap th,.bwrap td{padding:.75rem .9rem;text-align:left;border-bottom:1px solid var(--border);vertical-align:top;color:var(--gray-lt)}
.bwrap th{font-family:var(--heading);font-weight:700;color:var(--white);background:var(--card2);font-size:.82rem;letter-spacing:.04em;text-transform:uppercase}
.bwrap tr.hl td{background:var(--gold-faint);color:var(--white)}
.callout{background:var(--card);border:1px solid var(--gold-border);border-radius:var(--r);padding:1.25rem 1.5rem;margin:1.75rem 0}
.callout-title{font-family:var(--heading);font-weight:700;color:var(--gold);font-size:.85rem;letter-spacing:.08em;text-transform:uppercase;margin-bottom:.5rem}
.callout p:last-child{margin-bottom:0}
.faq details{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:0 1.25rem;margin-bottom:.6rem}
.faq summary{cursor:pointer;font-family:var(--heading);font-weight:600;color:var(--white);padding:1rem 0;list-style:none;position:relative;padding-right:2rem;font-size:.98rem}
.faq summary::after{content:"+";position:absolute;right:0;top:.9rem;color:var(--gold);font-size:1.3rem}
.faq details[open] summary::after{content:"–"}
.faq details p{padding-bottom:1rem;margin:0;font-size:.95rem}
.bcta{margin:3rem 0 2rem;padding:2rem;border-radius:var(--r-lg);background:linear-gradient(135deg,var(--card2),var(--card));border:1px solid var(--gold-border);text-align:center}
.bcta h2{margin:0 0 .6rem;font-size:1.5rem}
.bcta p{margin:0 auto 1.25rem;max-width:520px}
.bcta .btns{display:flex;flex-wrap:wrap;gap:.75rem;justify-content:center}
.author{display:flex;gap:1rem;align-items:center;padding:1.25rem;background:var(--card);border:1px solid var(--border);border-radius:var(--r);margin-top:2rem}
.author-av{width:48px;height:48px;border-radius:50%;background:var(--gold);color:#000;display:flex;align-items:center;justify-content:center;font-family:var(--heading);font-weight:800;flex-shrink:0}
.author-name{font-family:var(--heading);font-weight:700;color:var(--white)}
.author-role{font-size:.85rem;color:var(--muted)}
.posts{display:grid;gap:1rem;margin-top:2.5rem}
.post{display:block;background:var(--card);border:1px solid var(--border);border-radius:var(--r-lg);padding:1.5rem;text-decoration:none;transition:border-color .2s,transform .2s}
.post:hover{border-color:var(--gold-border);transform:translateY(-2px)}
.post-cat{font-size:.68rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--gold)}
.post h2{font-size:1.2rem;margin:.5rem 0 .5rem;color:var(--white)}
.post p{font-size:.95rem;margin:0 0 .75rem;color:var(--muted)}
.post-meta{font-size:.78rem;color:var(--muted2)}
@media(max-width:640px){.bwrap{padding-top:6rem}.bwrap table{display:block;overflow-x:auto}}
"""

def esc(s): return html.escape(s, quote=True)

def parts():
    home = HOME.read_text(encoding="utf-8")
    css = re.search(r"<style>(.*?)</style>", home, re.S).group(1)
    fonts = re.search(r'<link rel="preconnect" href="https://fonts.googleapis.com">.*?</noscript>', home, re.S).group(0)
    wa = re.search(r"<!-- WA FAB -->.*?</a>\n", home, re.S).group(0)
    mob = re.search(r'<!-- MOBILE MENU -->.*?</div>\n', home, re.S).group(0)
    nav = re.search(r'<!-- NAV -->.*?</nav>', home, re.S).group(0)
    footer = re.search(r"<footer>.*?</footer>", home, re.S).group(0)
    script = re.search(r"<script>\nconst nav.*?</script>", home, re.S).group(0)
    return css, fonts, wa, mob, nav, footer, script

def head(title, desc, url, schema_json, ogtype="article"):
    css, fonts, *_ = parts()
    return (
      '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
      f'<title>{esc(title)}</title>\n<meta name="description" content="{esc(desc)}">\n'
      '<meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large">\n'
      f'<link rel="canonical" href="{url}">\n'
      f'<meta property="og:type" content="{ogtype}"><meta property="og:site_name" content="Brandex"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{url}"><meta property="og:image" content="{BASE}/img/logo.png">\n'
      f'<meta name="twitter:card" content="summary"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}">\n'
      '<meta name="theme-color" content="#0a0a0a">\n<link rel="icon" type="image/png" href="/img/favicon.png">\n'
      f'{fonts}\n<script type="application/ld+json">\n{schema_json}\n</script>\n'
      f'<style>{css}{ARTICLE_CSS}</style></head><body>\n'
    )

def shell(inner_main):
    css, fonts, wa, mob, nav, footer, script = parts()
    return wa + mob + nav + "\n" + inner_main + "\n" + footer + "\n" + script + "\n</body></html>"

def main(spec_path):
    spec = json.load(open(spec_path))
    for k in ["slug","seo_title","h1","description","category","date","read_min","lead","body","faqs","card_blurb","llms_blurb"]:
        if k not in spec: sys.exit(f"spec missing: {k}")
    slug = spec["slug"]; assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug), "bad slug"
    url = f"{BASE}/blog/{slug}"
    title = f'{spec["seo_title"].strip()} | Brandex'
    assert len(title) <= 65, f"title too long ({len(title)}): {title}"
    desc = spec["description"].strip(); assert 110 <= len(desc) <= 165, f"description length {len(desc)}"
    d = datetime.date.fromisoformat(spec["date"]); date_long = d.strftime("%-d %B %Y"); date_short = d.strftime("%-d %b %Y")
    faqs = spec["faqs"]; assert 3 <= len(faqs) <= 7
    words = len(re.sub(r"<[^>]+>", " ", spec["lead"] + spec["body"]).split())

    schema = {"@context":"https://schema.org","@graph":[
      {"@type":"BlogPosting","@id":url+"#article","headline":spec["h1"],"description":desc,
       "datePublished":spec["date"],"dateModified":spec["date"],"inLanguage":"en-IN",
       "mainEntityOfPage":{"@type":"WebPage","@id":url},
       "author":{"@type":"Organization","name":"Brandex","url":BASE+"/"},
       "publisher":{"@type":"Organization","name":"Brandex","url":BASE+"/","logo":{"@type":"ImageObject","url":BASE+"/img/logo.png"}},
       "image":BASE+"/img/logo.png","articleSection":spec["category"],"wordCount":words,
       "about":{"@type":"Thing","name":"Personal branding in Chennai"},
       "speakable":{"@type":"SpeakableSpecification","cssSelector":["h1",".lead"]}},
      {"@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":1,"name":"Home","item":BASE+"/"},
        {"@type":"ListItem","position":2,"name":"Blog","item":BASE+"/blog/"},
        {"@type":"ListItem","position":3,"name":spec["h1"],"item":url}]},
      {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":f["q"],"acceptedAnswer":{"@type":"Answer","text":f["a"]}} for f in faqs]}
    ]}
    schema_json = json.dumps(schema, ensure_ascii=False).replace("</", "<\\/")

    faq_html = "\n".join(f'<details{" open" if i==0 else ""}><summary>{esc(f["q"])}</summary><p>{esc(f["a"])}</p></details>' for i,f in enumerate(faqs))
    main_html = (
      '<main class="bwrap"><article>\n'
      f'<span class="eyebrow">{esc(spec["category"])} · Chennai</span>\n<h1>{esc(spec["h1"])}</h1>\n'
      f'<div class="bmeta"><span>Brandex Studio, Valasaravakkam</span><span>{date_long}</span><span>{int(spec["read_min"])} min read</span></div>\n'
      f'<p class="lead">{spec["lead"].strip()}</p>\n{spec["body"].strip()}\n'
      '<h2>Frequently asked questions</h2>\n<div class="faq">\n' + faq_html + '\n</div>\n'
      '<div class="bcta"><h2>Want to see how this looks for you?</h2>'
      '<p>Talk to Yamini at Brandex. We\'ll go through your goals, show you recent shoots from professionals in your field, and book your first studio session in Valasaravakkam.</p>'
      '<div class="btns"><a href="https://wa.me/917448382828" class="btn btn-wa" target="_blank" rel="noopener">WhatsApp +91 74483 82828</a>'
      '<a href="mailto:hi@brandexpro.in" class="btn btn-outline">hi@brandexpro.in</a>'
      '<a href="/#contact-cta" class="btn btn-gold-primary">Book a session</a></div></div>\n'
      '<div class="author"><div class="author-av">B</div><div><div class="author-name">Brandex Studio Team</div>'
      '<div class="author-role">Chennai\'s dedicated personal branding studio · Script, shoot, edit and publish for doctors, founders and professionals</div></div></div>\n'
      '</article></main>'
    )
    (ROOT / "blog" / f"{slug}.html").write_text(head(title, desc, url, schema_json) + shell(main_html), encoding="utf-8")

    idx_p = ROOT / "blog" / "index.html"; idx = idx_p.read_text(encoding="utf-8")
    idx = re.sub(rf'<a href="/blog/{re.escape(slug)}" class="post">.*?</a>', "", idx, flags=re.S)
    card = (f'<a href="/blog/{slug}" class="post"><span class="post-cat">{esc(spec["category"])}</span><h2>{esc(spec["h1"])}</h2>'
            f'<p>{esc(spec["card_blurb"].strip())}</p><span class="post-meta">{date_short} · {int(spec["read_min"])} min read</span></a>')
    assert '<div class="posts">' in idx
    idx_p.write_text(idx.replace('<div class="posts">', '<div class="posts">' + card, 1), encoding="utf-8")

    sm_p = ROOT / "sitemap.xml"; sm = sm_p.read_text(encoding="utf-8")
    sm = re.sub(rf"\s*<url>\s*<loc>{re.escape(url)}</loc>.*?</url>", "", sm, flags=re.S)
    entry = f"  <url>\n    <loc>{url}</loc>\n    <lastmod>{spec['date']}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.7</priority>\n  </url>\n"
    sm = sm.replace("</urlset>", entry + "</urlset>")
    sm = re.sub(r"(<loc>https://www\.brandexpro\.in/blog/</loc>\s*<lastmod>)[^<]+", rf"\g<1>{spec['date']}", sm)
    sm_p.write_text(sm, encoding="utf-8")

    ll_p = ROOT / "llms.txt"; ll = ll_p.read_text(encoding="utf-8")
    ll = "\n".join(l for l in ll.split("\n") if f"]({url})" not in l)
    line = f"- [{spec['h1']}]({url}): {spec['llms_blurb'].strip()}"
    m = re.search(r"^## Blog\s*\n(?:.*\n)*?(?=\n## |\Z)", ll, re.M)
    ll = (ll[:m.start()] + m.group(0).rstrip("\n") + "\n" + line + "\n" + ll[m.end():]) if m else ll.rstrip("\n") + "\n\n## Blog\n" + line + "\n"
    ll_p.write_text(ll, encoding="utf-8")
    print(f"OK  {url}  ({words} words)")

if __name__ == "__main__":
    main(sys.argv[1])
