# Dusur website · موقع دسر

A fast, bilingual (Arabic / English) site with dark and light themes and a filterable "Our work" section.
No framework, no database. A small Python script turns the text files in `content/` into plain pages in `docs/`, which GitHub Pages serves.

## ابدأ بسرعة (بالعربي)

1. افتح `content/site.yaml` وغيّر `site_url` إلى رابط موقعك الحقيقي (مثال: `https://abdo.github.io/dusur`). **مهم** للبحث ولمعاينة الروابط.
2. ضع روابط حساباتك (انستغرام / فيسبوك / يوتيوب) في نفس الملف. الأيقونات لا تظهر إلا لما تكتب الرابط.
3. شغّل الأمر: `python build.py` (بعد `pip install -r requirements.txt` لأول مرة).
4. ارفع مجلد المشروع كله على GitHub، ومن **Settings → Pages** اختر `Deploy from a branch` ثم `main` و `/docs`.
5. النصوص العربية والإنجليزية في `content/ui.ar.yaml` و `content/ui.en.yaml`. لو نقص مفتاح في أحدهما، البناء يتوقف ويقول لك أيهما.
6. لإضافة مشروع حقيقي: انسخ صورته إلى `media/projects/<id>.jpg`، وملفه (اختياري) إلى `files/<id>.pdf`، وغيّر `status: concept` إلى `status: completed` في `content/projects.yaml`، ثم `python build.py`.

> كل المشاريع الحالية **تصورات تصميمية** ومكتوب عليها ذلك صراحةً. غيّرها إلى `completed` فقط لما تكون أعمالاً منفذة فعلاً.

---

## What is where

| Path | What it is |
| --- | --- |
| `content/site.yaml` | Site address, WhatsApp / phone, social links, theme colours, which drawing each section picture uses |
| `content/ui.ar.yaml`, `content/ui.en.yaml` | Every piece of text, per language (titles, SEO descriptions, buttons, schema text) |
| `content/projects.yaml` | The projects (data only, separate from the design) |
| `content/sectors.yaml` | The filter categories |
| `media/projects/`, `media/site/` | Your real photos (optional) |
| `files/` | Downloadable files, such as PDFs (optional) |
| `assets/css/main.css` | All styling. Colours for both themes are at the top |
| `assets/js/` | `boot.js` (theme + language, runs first), `main.js` (page behaviour), `portfolio.js` (filters + preview window, loaded only when needed) |
| `templates/` | Page and component templates (header, footer, project card, preview window, etc.) |
| `build/placeholders.py` | Draws the placeholder pictures |
| `build.py` | The build script |
| `docs/` | **The finished site.** This is the folder GitHub Pages publishes. Do not edit by hand; it is rebuilt each time |

## Everyday commands

```bash
pip install -r requirements.txt     # first time only
python build.py                     # rebuild into docs/
python build.py --serve             # rebuild and preview at http://localhost:8000
```

Preview over a local server (as above), not by double-clicking `index.html`: the "Our work" code is loaded as a separate module, and browsers block that on `file://`.

## Add a project

Add a block to `content/projects.yaml` (copy an existing one and change it):

```yaml
- id: oak-kitchen-maadi          # lowercase English words with dashes; also names the files
  sector: kitchens               # one of the ids in sectors.yaml
  status: completed              # concept | completed
  placeholder: {kind: kitchen, tone: oak}
  titleAr: ...
  titleEn: ...
  descriptionAr: ...
  descriptionEn: ...
  highlightsAr: [..., ..., ...]
  highlightsEn: [..., ..., ...]
```

Then drop the files next to it and rebuild:

* Photo: `media/projects/oak-kitchen-maadi.jpg` (png / webp also work). The build makes AVIF, WebP and JPEG at 480, 800 and 1200 px, and the photo fades in over the drawing without moving the page.
* Download: `files/oak-kitchen-maadi.pdf` (any extension). Without a file, the button shows a clear "Soon" state and a short message.
* Full preview (3D viewer, video, PDF): set `previewUrl:` to a link or to a file inside `files/`.

Use a photo around 1600 px wide, 4:3 if you can. Every picture is shown in a fixed 4:3 frame.

The placeholder drawings come in 10 kinds (`kitchen`, `dressing`, `tv`, `bath`, `joinery`, `restaurant`, `cafe`, `shop`, `cladding`, `fitout`) and 6 tones (`walnut`, `ebony`, `oak`, `linen`, `copper`, `moss`). Each project gets its own variation, so no two look the same.

## Add a sector or change the text

* Sectors: edit `content/sectors.yaml` (`id`, `kind`, `nameAr`, `nameEn`). A sector with no projects is hidden from the filter.
* Text: edit both `ui.ar.yaml` and `ui.en.yaml`. The build checks that both files have the same keys and stops if they differ.
* Colours: edit the two theme blocks at the top of `assets/css/main.css`, and `theme_color_dark` / `theme_color_light` in `site.yaml`.

## Deploy on GitHub Pages

1. Create a repository, upload this whole folder (including `docs/`).
2. **Settings → Pages → Build and deployment**: Source `Deploy from a branch`, Branch `main`, folder `/docs`.
3. Set `site_url` in `content/site.yaml` to the address GitHub shows (for a project site it ends with the repository name), run `python build.py`, commit and push.

All links are relative, so the site also works under a sub-path such as `username.github.io/dusur/`.

Custom domain: put your domain in `docs/CNAME` (the build keeps this file), set `site_url` to `https://your-domain`, rebuild.

## How the languages work

* Arabic is the main page at `/`, English is at `/en/`. They are two real pages, so search engines index both, and they point to each other with `hreflang`.
* The AR / EN switch remembers the choice. A returning visitor lands on their language. Search engines never get redirected.
* The theme follows the visitor's system setting until they press the sun / moon button; after that their choice is remembered.

## SEO, performance, accessibility (already handled)

* Unique title and description per language, canonical, `hreflang`, Open Graph, Twitter card, `sitemap.xml`, `robots.txt`, and Schema.org data (Organization, WebSite, WebPage, Services). Projects are added to the schema only when `status: completed`, so design concepts are never presented as delivered work.
* Each page is about 18 KB gzipped including all CSS and the page script. The portfolio code is a separate small file loaded only when the visitor nears "Our work". Images are lazy, sized by `srcset`, and sit in fixed 4:3 frames (no layout shift).
* Respects `prefers-reduced-motion`. Keyboard friendly (focus order, Esc closes the preview, arrow keys step through projects, direction-aware in Arabic). Contrast meets WCAG AA in both themes.

## Fonts

The site uses **Readex Pro** (Arabic + Latin) from Google Fonts, loaded without blocking the page, with system fonts as the fallback. If you prefer to host the font yourself later, download the variable font, place it in `assets/fonts/`, add an `@font-face` to `main.css`, and remove the `font_css` link in `templates/base.html`.

## Before you publish: checklist

- [ ] `site_url` set in `content/site.yaml` (the build prints a warning until you do)
- [ ] Social links added (optional)
- [ ] Real photos added as you finish projects, and `status` changed to `completed`
- [ ] `python build.py`, then commit and push `docs/`
