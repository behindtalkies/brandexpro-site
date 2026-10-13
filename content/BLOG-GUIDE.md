# Brandex (brandexpro.in) blog publishing guide

Standing brief for every automated blog run. Follow it exactly.

## Who we are (facts you may state)
- Brandex is a dedicated personal branding studio in Chennai, at #5 Velan Nagar Second Street, Valasaravakkam, Chennai 600087. Service is for professionals in and around Chennai only.
- Clients: doctors and specialists, dentists, entrepreneurs and founders, chartered accountants, lawyers/advocates, financial advisors, educators, architects, consultants, IT professionals, business owners.
- End-to-end: script writing → studio-grade shooting (cinema cameras, advanced lighting, B-roll) → cinematic editing → publishing to YouTube, Instagram and Facebook. Batch shoot days produce many videos from one session.
- Team: Shankar (Creative Director), Vaishalini (Creative Head), Mathews (Senior DOP), Priya (Associate Producer), Muthu and Rajesh (Video Editors), SK (Jr DOP). You may mention roles; keep it light.
- Social proof allowed: "20+ clients", "1K+ videos published". Do not invent client names or results.
- Contact for every CTA: **Yamini** — hi@brandexpro.in, WhatsApp +91 74483 82828, or the booking form on the home page (`/#contact-cta`). The post template adds this CTA automatically; do not add a second one.

## Hard rules
1. **Never state prices** — not in rupees, not "starting at", not per-video or per-month figures, not even ranges. Pricing is discussed on a call. `scripts/check.py` blocks rupee amounts and price patterns. You may say what *changes* the cost (number of videos, shoot days, locations, editing style) without numbers.
2. **Never name real creators, influencers, celebrities or other local studios/agencies.** Describe styles ("cinematic talking-head", "bold-caption reels"). Never compare against named competitors.
3. Chennai only. Never pitch to overseas clients, never mention BrandexVideo or remote editing. Chennai neighbourhoods (Anna Nagar, Adyar, OMR, Velachery, T. Nagar, Nungambakkam, Porur, Tambaram…) are welcome where natural.
4. Medical and legal content: respect Indian professional advertising rules — doctors cannot make superiority/guarantee claims or use patient testimonials for solicitation (NMC guidelines); advocates face Bar Council restrictions on advertising. Frame video as education and trust-building, never as "get more patients fast" promises.
5. No fabricated statistics. Use a number only if found on a credible page during this run's research; otherwise write qualitatively.
6. SEO title ≤ 55 characters before the automatic " | Brandex" suffix. Meta description 120–160 characters, answer-first, with the keyword.
7. Answer-first lead: 2–3 sentences that directly answer the keyword's question, key phrase in `<strong>`.
8. Length 900–1,300 words (lead + body). 4–6 H2 sections matching real sub-questions. One `<table>` or `<div class="callout">` where it genuinely helps.
9. 4–6 FAQs in "People also ask" style; each answer 1–3 self-contained sentences (used in FAQPage schema).
10. Internal links: at least 2 links to the home page sections (`/#services`, `/#for-who`, `/#team`, `/#faq`, `/#contact-cta`) and at least 1 link to another `/blog/` post that exists in the repo (check `blog/` first). Only link to pages that exist.
11. Tone: warm, direct, practical, Chennai-aware. Indian English spelling (colour, organise). Short paragraphs. No filler intros, no "In today's digital world". Write like the studio team talking to a busy professional.
12. `date` is today's date in Asia/Kolkata.

## Allowed HTML inside `body`
`<h2>`, `<h3>`, `<p>`, `<strong>`, `<em>`, `<a href="/...">`, `<ul>/<ol>/<li>`, `<table><thead>…</thead><tbody>…<tr class="hl">…</tr></tbody></table>`, `<div class="callout"><div class="callout-title">…</div><p>…</p></div>`. No images, scripts or inline styles.

## Run procedure (every scheduled run)
1. Attach and clone `behindtalkies/brandexpro-site` (push access). Work on `main`.
2. Open `content/keyword-queue.md`. Take the first `- [ ]` line (two lines on a 2-post run). Parse slug, keyword, H1, category.
3. Research the keyword with 3–5 web searches (intent, People-also-ask, any current figures, what top results miss). Effort goes into the content, not the research.
4. Write the spec JSON to `content/drafts/<slug>.json` (fields in `scripts/new_post.py` docstring).
5. Run `python3 scripts/new_post.py content/drafts/<slug>.json`.
6. Run `python3 scripts/check.py`; fix until `ALL CHECKS PASSED`. Never push with failures.
7. Mark the queue line `- [x] YYYY-MM-DD`.
8. `git add -A && git commit -m "Blog: <H1>" && git push origin main`. Netlify deploys automatically.
9. Wait 120 s, fetch `https://www.brandexpro.in/blog/<slug>?v=<random>` and confirm the H1 is present; retry once after 120 s; otherwise report.
10. Final message: title, live URL, keyword, links used, next queued keyword.

## If something is wrong
- Queue empty / under 6 lines → append 10 new lines in the same format across the section themes, commit, continue.
- Script errors → fix the spec, not the scripts, unless a script is itself broken (say so).
- Push rejected → `git pull --rebase origin main`, push once more.
