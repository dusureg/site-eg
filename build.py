#!/usr/bin/env python3
"""
Dusur site builder.

    python build.py            # build the site into docs/
    python build.py --serve    # build, then preview at http://localhost:8000

What it does
  * renders the Arabic page (docs/index.html) and the English page (docs/en/index.html)
  * generates the placeholder drawings, and turns any real photos you drop into media/ into
    responsive AVIF / WebP / JPEG files
  * writes the SEO files: sitemap.xml, robots.txt, 404.html, structured data (JSON-LD)
  * checks that the Arabic and English text files match, so nothing is left untranslated
"""
import argparse
import datetime
import gzip
import hashlib
import http.server
import json
import re
import shutil
import socketserver
import sys
import urllib.parse
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "build"))
from placeholders import PALETTES, SCENES, make_placeholder  # noqa: E402

LANGS = ("ar", "en")
NAV_ORDER = ["services", "work", "business", "contracting", "contact"]
SVC_KEYS = ["svc-kitchen", "svc-dressing", "svc-tv", "svc-bath", "svc-joinery"]
BIZ_KEYS = ["biz-restaurant", "biz-cafe", "biz-shop"]
CON_KEYS = ["con-woodwork", "con-fitout"]
FONT_CSS = "https://fonts.googleapis.com/css2?family=Readex+Pro:wght@300..700&display=swap"
IMG_WIDTHS = (480, 800, 1200)
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp", ".avif")

warnings, errors = [], []


# ── small helpers ────────────────────────────────────────────────────────────
def load_yaml(name):
    return yaml.safe_load((ROOT / "content" / name).read_text(encoding="utf-8"))


def flat_keys(d, p=""):
    """Every key path in a nested structure, with list lengths, for the translation check."""
    out = []
    if isinstance(d, dict):
        for k, v in d.items():
            out += flat_keys(v, f"{p}.{k}" if p else str(k))
    elif isinstance(d, list):
        out.append(f"{p}[{len(d)}]")
        for i, v in enumerate(d):
            out += flat_keys(v, f"{p}[{i}]")
    else:
        out.append(p)
    return out


def min_css(s):
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s*([{};,>])\s*", r"\1", s)
    s = re.sub(r"\s*:\s*", ":", s)
    s = s.replace(";}", "}")
    return s.strip()


def min_js(s):
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    out = []
    for line in s.split("\n"):
        line = re.sub(r"^\s*//.*$", "", line)          # whole-line comments
        line = re.sub(r"\s+//[^\n'\"`]*$", "", line)   # trailing comments (no URLs in our strings)
        line = line.strip()
        if line:
            out.append(line)
    return "\n".join(out)


def tidy_html(h):
    h = re.sub(r"\n[ \t]+", "\n", h)
    return re.sub(r"\n{2,}", "\n", h).strip() + "\n"


def find_media(folder, stem):
    d = ROOT / "media" / folder
    for ext in IMG_EXT:
        for cand in (d / f"{stem}{ext}", d / f"{stem}{ext.upper()}"):
            if cand.exists():
                return cand
    return None


# ── load + validate content ──────────────────────────────────────────────────
site = load_yaml("site.yaml")
sectors = load_yaml("sectors.yaml")
projects = load_yaml("projects.yaml")
ui = {lang: load_yaml(f"ui.{lang}.yaml") for lang in LANGS}

site["site_url"] = str(site["site_url"]).rstrip("/")
if "YOUR-USERNAME" in site["site_url"]:
    warnings.append("site_url in content/site.yaml is still the example address. Canonical links, hreflang, "
                    "the sitemap and share previews will point to the wrong place until you set it.")

a, b = set(flat_keys(ui["ar"])), set(flat_keys(ui["en"]))
for k in sorted(a - b):
    errors.append(f"Missing in ui.en.yaml: {k}")
for k in sorted(b - a):
    errors.append(f"Missing in ui.ar.yaml: {k}")

sector_ids = [s["id"] for s in sectors]
if len(set(sector_ids)) != len(sector_ids):
    errors.append("sectors.yaml has duplicate ids")
seen = set()
for p in projects:
    pid = p.get("id", "?")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", str(pid)):
        errors.append(f"Project id '{pid}' must be lowercase English words joined by dashes")
    if pid in seen:
        errors.append(f"Duplicate project id '{pid}'")
    seen.add(pid)
    if p.get("sector") not in sector_ids:
        errors.append(f"Project '{pid}': unknown sector '{p.get('sector')}'")
    for f in ("titleAr", "titleEn", "descriptionAr", "descriptionEn", "highlightsAr", "highlightsEn"):
        if not p.get(f):
            errors.append(f"Project '{pid}': '{f}' is empty")
    if p.get("status", "concept") not in ("concept", "completed"):
        errors.append(f"Project '{pid}': status must be 'concept' or 'completed'")
    ph = p.get("placeholder") or {}
    if ph.get("kind") and ph["kind"] not in SCENES:
        errors.append(f"Project '{pid}': placeholder kind '{ph['kind']}' is not one of {sorted(SCENES)}")
    if ph.get("tone") and ph["tone"] not in PALETTES:
        errors.append(f"Project '{pid}': placeholder tone '{ph['tone']}' is not one of {sorted(PALETTES)}")
for key, spec in site["section_media"].items():
    if spec["kind"] not in SCENES or spec.get("tone") not in PALETTES:
        errors.append(f"site.yaml section_media '{key}': check kind/tone")

if errors:
    print("\nThe build stopped. Please fix:\n  - " + "\n  - ".join(errors))
    sys.exit(1)

# ── output folder (keeps a CNAME file if you added one) ──────────────────────
ap = argparse.ArgumentParser()
ap.add_argument("--out", default="docs")
ap.add_argument("--serve", action="store_true")
ap.add_argument("--port", type=int, default=8000)
args = ap.parse_args()
OUT = (ROOT / args.out).resolve()
cname = (OUT / "CNAME").read_text() if (OUT / "CNAME").exists() else None
if OUT.exists():
    shutil.rmtree(OUT)
(OUT / "assets" / "ph").mkdir(parents=True)
(OUT / "assets" / "js").mkdir(parents=True)
(OUT / "assets" / "img").mkdir(parents=True)
(OUT / "en").mkdir()
(OUT / ".nojekyll").write_text("")
if cname:
    (OUT / "CNAME").write_text(cname)

# ── static assets ────────────────────────────────────────────────────────────
shutil.copytree(ROOT / "assets" / "brand", OUT / "assets" / "brand", ignore=shutil.ignore_patterns("originals", "glyph-d.svg"))

portfolio_src = min_js((ROOT / "assets" / "js" / "portfolio.js").read_text(encoding="utf-8"))
(OUT / "assets" / "js" / "portfolio.js").write_text(portfolio_src, encoding="utf-8")
portfolio_path = "assets/js/portfolio.js?v=" + hashlib.md5(portfolio_src.encode()).hexdigest()[:8]

css = min_css((ROOT / "assets" / "css" / "main.css").read_text(encoding="utf-8"))


def fill_tokens(js):
    return (js.replace("__LIGHT__", site["theme_color_light"]).replace("__DARK__", site["theme_color_dark"]))


boot_js = min_js(fill_tokens((ROOT / "assets" / "js" / "boot.js").read_text(encoding="utf-8")))
main_js_tpl = min_js(fill_tokens((ROOT / "assets" / "js" / "main.js").read_text(encoding="utf-8")))

# ── placeholder art: one drawing per project and per section picture ─────────
ph_keys = {}
for key, spec in site["section_media"].items():
    ph_keys[f"site/{key}"] = (spec["kind"], spec.get("tone"))
sector_kind = {s["id"]: s["kind"] for s in sectors}
for p in projects:
    ph = p.get("placeholder") or {}
    ph_keys[f"projects/{p['id']}"] = (ph.get("kind") or sector_kind[p["sector"]], ph.get("tone"))
for key, (kind, tone) in ph_keys.items():
    svg = make_placeholder(kind, key=key, tone=tone)
    (OUT / "assets" / "ph" / (key.replace("/", "-") + ".svg")).write_text(svg, encoding="utf-8")

# ── real photos -> responsive AVIF / WebP / JPEG ─────────────────────────────
images = {}      # key -> dict(stem, w, h, files{ext:{width:filename}})


def process_image(key, src):
    stem = key.replace("/", "-")
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    ow, oh = im.size
    widths = sorted({w for w in IMG_WIDTHS if w <= ow} or {ow})
    if ow > IMG_WIDTHS[-1] and IMG_WIDTHS[-1] not in widths:
        widths.append(IMG_WIDTHS[-1])
    files = {"avif": {}, "webp": {}, "jpg": {}}
    for w in widths:
        h = round(oh * w / ow)
        r = im.resize((w, h), Image.LANCZOS) if w != ow else im
        for ext, kw in (("avif", dict(quality=55, speed=6)), ("webp", dict(quality=78, method=5)),
                        ("jpg", dict(quality=80, optimize=True, progressive=True))):
            name = f"{stem}-{w}.{ext}"
            try:
                r.save(OUT / "assets" / "img" / name, "JPEG" if ext == "jpg" else ext.upper(), **kw)
                files[ext][w] = name
            except Exception as e:      # an encoder may be missing on this machine
                if ext != "jpg":
                    warnings.append(f"Could not write {ext} for {src.name} ({e}); JPEG is still used.")
                else:
                    raise
    tw = widths[-1]
    images[key] = dict(w=tw, h=round(oh * tw / ow), files=files, widths=widths)


for p in projects:
    key = f"projects/{p['id']}"
    src = (ROOT / "media" / "projects" / p["image"]) if p.get("image") else find_media("projects", p["id"])
    if src and src.exists():
        process_image(key, src)
    elif p.get("image"):
        warnings.append(f"Project '{p['id']}': image '{p['image']}' was not found in media/projects/")
for key in site["section_media"]:
    src = find_media("site", key)
    if src:
        process_image(f"site/{key}", src)

known = {p["id"] for p in projects}
for f in (ROOT / "media" / "projects").glob("*"):
    if f.is_file() and f.suffix.lower() in IMG_EXT and f.stem not in known and f.name not in {str(p.get("image") or "") for p in projects}:
        warnings.append(f"media/projects/{f.name} does not match any project id, so it is not used.")
for f in (ROOT / "media" / "site").glob("*"):
    if f.is_file() and f.suffix.lower() in IMG_EXT and f.stem not in site["section_media"]:
        warnings.append(f"media/site/{f.name} does not match a picture name in site.yaml, so it is not used.")


def make_media_info(base):
    def media_info(key):
        im = images.get(key)
        if not im:
            return None
        def srcset(ext):
            return ", ".join(f"{base}assets/img/{n} {w}w" for w, n in im["files"][ext].items())
        sources = [dict(type=f"image/{e}", srcset=srcset(e)) for e in ("avif", "webp") if im["files"][e]]
        jpg = im["files"]["jpg"]
        mid = jpg[sorted(jpg)[len(jpg) // 2]]
        return dict(sources=sources, srcset=srcset("jpg"), src=f"{base}assets/img/{mid}", w=im["w"], h=im["h"])
    return media_info


# ── downloadable files ───────────────────────────────────────────────────────
(OUT / "files").mkdir(exist_ok=True)
file_of = {}       # project id -> path relative to site root (or an external URL)
preview_of = {}


def copy_file(name):
    src = ROOT / "files" / name
    if src.exists():
        dst = OUT / "files" / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return "files/" + name
    return None


for p in projects:
    dl = (p.get("downloadUrl") or "").strip()
    if dl:
        if re.match(r"^(https?:)?//", dl):
            file_of[p["id"]] = dl
        else:
            got = copy_file(dl.removeprefix("files/"))
            if got:
                file_of[p["id"]] = got
            else:
                warnings.append(f"Project '{p['id']}': downloadUrl '{dl}' was not found in files/")
    else:
        for f in sorted((ROOT / "files").glob(f"{p['id']}.*")):
            file_of[p["id"]] = copy_file(f.name)
            break
    pv = (p.get("previewUrl") or "").strip()
    if pv:
        if re.match(r"^(https?:)?//", pv):
            preview_of[p["id"]] = pv
        else:
            got = copy_file(pv.removeprefix("files/"))
            if got:
                preview_of[p["id"]] = got
            else:
                warnings.append(f"Project '{p['id']}': previewUrl '{pv}' was not found in files/")
if not any((OUT / "files").iterdir()):
    (OUT / "files").rmdir()


# ── templating ───────────────────────────────────────────────────────────────
env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape(["html"]),
                  trim_blocks=True, lstrip_blocks=True)
SITE = site["site_url"]
YEAR = datetime.date.today().year
TODAY = datetime.date.today().isoformat()


def wa_link(msg):
    return f"https://wa.me/{site['whatsapp']}?text={urllib.parse.quote(msg)}"


def socials_for(t):
    out = []
    for name, icon in (("instagram", "ig"), ("facebook", "fb"), ("youtube", "yt")):
        url = (site.get("social") or {}).get(name)
        if url:
            out.append(dict(url=url, icon=icon, label=t["contact"][name]))
    return out


def json_ld(lang, t, canonical, socials, completed):
    org_id, web_id = f"{SITE}/#organization", f"{SITE}/#website"
    og = f"{SITE}/assets/brand/og-image.jpg"
    org = {"@type": "Organization", "@id": org_id, "name": t["meta"]["site_name"], "alternateName": ["Dusur", "دسر"],
           "url": f"{SITE}/", "logo": {"@type": "ImageObject", "url": f"{SITE}/assets/brand/icon-512.png", "width": 512, "height": 512},
           "image": og, "description": t["schema"]["org_description"], "telephone": site["phone_e164"],
           "areaServed": {"@type": "Country", "name": "Egypt"},
           "contactPoint": [{"@type": "ContactPoint", "telephone": site["phone_e164"], "contactType": "customer service",
                             "areaServed": site["country"], "availableLanguage": ["Arabic", "English"]}]}
    if socials:
        org["sameAs"] = [s["url"] for s in socials]
    graph = [
        org,
        {"@type": "WebSite", "@id": web_id, "url": f"{SITE}/", "name": t["meta"]["site_name"], "inLanguage": ["ar", "en"], "publisher": {"@id": org_id}},
        {"@type": "WebPage", "@id": canonical + "#webpage", "url": canonical, "name": t["meta"]["title"], "description": t["meta"]["description"],
         "inLanguage": lang, "isPartOf": {"@id": web_id}, "about": {"@id": org_id}, "primaryImageOfPage": {"@type": "ImageObject", "url": og}},
        {"@type": "ItemList", "name": t["services"]["title"], "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "item": {"@type": "Service", "name": s["name"], "description": s["description"],
                                                               "provider": {"@id": org_id}, "areaServed": {"@type": "Country", "name": "Egypt"}}}
            for i, s in enumerate(t["schema"]["services"])]},
    ]
    if completed:      # only real, delivered projects are marked up; design concepts are not
        graph.append({"@type": "ItemList", "name": t["work"]["title"], "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "item": {"@type": "CreativeWork", "name": c["title"], "description": c["description"],
                                                               "creator": {"@id": org_id}, "inLanguage": lang}}
            for i, c in enumerate(completed)]})
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))


def localise_projects(lang, t, base):
    L = lang.capitalize()
    sector_name = {s["id"]: s["name" + L] for s in sectors}
    out = []
    for p in projects:
        status = p.get("status", "concept")
        label = t["work"]["completed" if status == "completed" else "concept"]
        title = p["title" + L]
        dl = file_of.get(p["id"])
        pv = preview_of.get(p["id"])
        out.append(dict(
            id=p["id"], sector=p["sector"], sector_name=sector_name[p["sector"]], status=status, status_label=label,
            title=title, description=p["description" + L], highlights=p["highlights" + L],
            alt=f"{title} — {label}",
            download=(dl if dl and re.match(r"^(https?:)?//", dl) else (base + dl if dl else None)),
            preview_url=(pv if pv and re.match(r"^(https?:)?//", pv) else (base + pv if pv else None)),
            ask_url=wa_link(t["work"]["ask_msg"].format(title=title)),
        ))
    return out


def render_home(lang):
    t = ui[lang]
    L = lang.capitalize()
    base = "" if lang == "ar" else "../"
    path = "" if lang == "ar" else "en/"
    canonical = f"{SITE}/{path}"
    ps = localise_projects(lang, t, base)
    counts = {}
    for p in ps:
        counts[p["sector"]] = counts.get(p["sector"], 0) + 1
    secs = [dict(id=s["id"], name=s["name" + L], count=counts[s["id"]]) for s in sectors if counts.get(s["id"])]
    socials = socials_for(t)
    urls = dict(self="#top", ar="./" if lang == "ar" else "../", en="en/" if lang == "ar" else "./",
                other="en/" if lang == "ar" else "../")
    seo = dict(title=t["meta"]["title"], description=t["meta"]["description"], canonical=canonical,
               image=f"{SITE}/assets/brand/og-image.jpg",
               alternates=[dict(hreflang="ar", href=f"{SITE}/"), dict(hreflang="en", href=f"{SITE}/en/"),
                           dict(hreflang="x-default", href=f"{SITE}/")])
    completed = [p for p in ps if p["status"] == "completed"]
    main_js = fill_base(main_js_tpl, base)
    tpl = env.get_template("home.html")
    html = tpl.render(lang=lang, dir=t["dir"], t=t, site=site, base=base, urls=urls, seo=seo, projects=ps, sectors=secs,
                      socials=socials, nav_order=NAV_ORDER, svc_keys=SVC_KEYS, biz_keys=BIZ_KEYS, con_keys=CON_KEYS,
                      year=YEAR, css=css, boot_js=boot_js, main_js=main_js, font_css=FONT_CSS,
                      jsonld=json_ld(lang, t, canonical, socials, completed), media_info=make_media_info(base),
                      wa_link=wa_link)
    return tidy_html(html)


def fill_base(js, base):
    # import() needs "./", "../" or an absolute URL in front of the path; a bare "assets/..." is rejected
    return js.replace("__BASE__", json.dumps(base or "./")).replace("__PORTFOLIO__", portfolio_path)


def render_404():
    t = ui["ar"]
    root = SITE + "/"
    seo = dict(title=f"{ui['ar']['notfound']['title']} · {ui['en']['notfound']['title']}", description="", canonical=root,
               image=f"{SITE}/assets/brand/og-image.jpg", alternates=[], noindex=True)
    html = env.get_template("404.html").render(
        lang="ar", dir="rtl", t=t, ar=ui["ar"], en=ui["en"], site=site, base=root, site_root=root,
        urls=dict(self=root, ar=root, en=root + "en/", other=""), seo=seo, projects=[], sectors=[], socials=[],
        nav_order=NAV_ORDER, year=YEAR, css=css, boot_js=boot_js, main_js=fill_base(main_js_tpl, root),
        font_css=FONT_CSS, jsonld=None, media_info=make_media_info(root), wa_link=wa_link)
    return tidy_html(html)


pages = {"index.html": render_home("ar"), "en/index.html": render_home("en"), "404.html": render_404()}
for name, html in pages.items():
    (OUT / name).write_text(html, encoding="utf-8")

# ── sitemap + robots ─────────────────────────────────────────────────────────
alts = "".join(f'<xhtml:link rel="alternate" hreflang="{h}" href="{u}"/>'
               for h, u in (("ar", f"{SITE}/"), ("en", f"{SITE}/en/"), ("x-default", f"{SITE}/")))
sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
           + "".join(f"<url><loc>{u}</loc><lastmod>{TODAY}</lastmod>{alts}</url>\n" for u in (f"{SITE}/", f"{SITE}/en/"))
           + "</urlset>\n")
(OUT / "sitemap.xml").write_text(sitemap, encoding="utf-8")
(OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")

# ── report ───────────────────────────────────────────────────────────────────
print("\nBuilt into", OUT.relative_to(ROOT) if ROOT in OUT.parents else OUT)
for name, html in pages.items():
    raw = len(html.encode())
    print(f"  {name:<14} {raw/1024:6.1f} KB   {len(gzip.compress(html.encode()))/1024:5.1f} KB gzipped")
print(f"  projects: {len(projects)}   sectors shown: {len({p['sector'] for p in projects})}   "
      f"real photos used: {len(images)}   downloadable files: {len(file_of)}")
for w in warnings:
    print("  ! " + w)

if args.serve:
    handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=str(OUT), **k)  # noqa: E731
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", args.port), handler) as srv:
        print(f"\nPreview: http://localhost:{args.port}/   (Ctrl+C to stop)")
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            pass
