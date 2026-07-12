
import os
import re
import json
import shutil

# Explicit paths mapping across your NVMe SSD and 1TB HDD storage
source_dir = os.path.dirname(os.path.abspath(__file__))
build_dir = os.path.join(os.path.dirname(source_dir), "dist")
assets_src = os.path.join(source_dir, "assets")  # In-repo media (committed to git); Cloudflare R2 planned for a later release
assets_dst = os.path.join(build_dir, "assets")

# Ensure the workspace directory exists
os.makedirs(os.path.dirname(build_dir), exist_ok=True)

# Clean and rebuild target distribution folder
if os.path.exists(build_dir):
    shutil.rmtree(build_dir)
os.makedirs(os.path.join(build_dir, "en"), exist_ok=True)
os.makedirs(os.path.join(build_dir, "ta"), exist_ok=True)

# Constructing regex with concatenation so chat UIs cannot mistakenly hide it
pattern_str = "<!" + "--#\\s*include\\s+virtual=[\"']([^\"']+)[\"']\\s*--" + ">"
ssi_pattern = re.compile(pattern_str)

def find_file(virtual_path):
    """Finds include files relative to the development source structure."""
    clean_path = virtual_path.lstrip('/')
    
    candidates = [
        os.path.join(source_dir, clean_path),
        os.path.join(source_dir, "parts", os.path.basename(clean_path)),
        os.path.join(source_dir, os.path.basename(clean_path))
    ]
    
    for candidate in candidates:
        if os.path.exists(candidate) and os.path.isfile(candidate):
            return candidate
    return None

def process_file(file_path):
    """Recursively parses HTML components, converting dynamic SSI to static layouts."""
    if not os.path.exists(file_path):
        print(f"⚠️ Warning: Component missing: {file_path}")
        return f""
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    def replace_match(match):
        if len(match.groups()) > 0:
            virtual_path = match.group(1)
            inc_file = find_file(virtual_path)
            if inc_file:
                print(f"  -> Merging component: {virtual_path}")
                return process_file(inc_file)
            else:
                print(f"  ❌ Error: Could not resolve component: {virtual_path}")
                return f""
        return match.group(0)
            
    # Bounded iteration safety net - completely prevents any chance of terminal hanging
    for _ in range(10):
        if not ssi_pattern.search(content):
            break
        content = ssi_pattern.sub(replace_match, content)
        
    return content

# ── Schools page generator ───────────────────────────────────────────
# The Schools (பள்ளிகள்) page is data-driven: cards are generated from
# html/data/schools.json at build time and injected where the marker
#   <!--#school-cards lang="en"-->  /  <!--#school-cards lang="ta"-->
# appears. Never hand-edit the cards in en/schools.html / ta/schools.html —
# edit the JSON (content) or SCHOOL_CARD_TEMPLATE (style) and rebuild.
schools_data_path = os.path.join(source_dir, "data", "schools.json")

SCHOOL_LABELS = {
    "en": {"est": "Est.", "students": "Students", "staff": "Staff", "chairman": "Chairman", "donate": "Donate"},
    "ta": {"est": "தொடக்கம்", "students": "மாணவர்கள்", "staff": "பணியாளர்கள்", "chairman": "தாளாளர்", "donate": "நன்கொடை"},
}

SCHOOL_CARD_TEMPLATE = """
        <article class="group relative flex-none w-[19rem] sm:w-[21rem] snap-start rounded-3xl overflow-hidden bg-slate-900 border border-white/10 shadow-xl flex flex-col">
          <div class="relative h-36 overflow-hidden hero-gradient">
            <div class="absolute inset-0 flex items-center justify-center">
              <svg class="w-14 h-14 text-white/20" fill="currentColor" viewBox="0 0 24 24"><path d="M12 3 1 8.5l11 5.5 9-4.5V17h2V8.5L12 3zM5 13.18v3.32L12 20l7-3.5v-3.32l-7 3.5-7-3.5z"/></svg>
            </div>
            {{#has_photo}}<img src="{{photo}}" alt="{{name}} — {{place}}" loading="lazy" class="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition duration-700">{{/has_photo}}
            <div class="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/50 to-transparent"></div>
            {{#year_started}}<span class="absolute top-3 right-3 text-[10px] font-bold uppercase tracking-widest bg-blue-500/90 text-white rounded-full px-2.5 py-1">{{est_label}} {{year_started}}</span>{{/year_started}}
          </div>
          <div class="relative flex flex-col flex-1 p-5">
            <h3 class="text-base font-black leading-snug text-white mb-1">{{name}}</h3>
            <p class="text-sm text-blue-300 font-semibold mb-3 flex items-start gap-1">
              <svg class="w-3.5 h-3.5 mt-0.5 flex-none" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5A2.5 2.5 0 1 1 12 6a2.5 2.5 0 0 1 0 5.5z"/></svg>
              <span>{{place}}</span></p>
            {{#students_total}}<div class="flex gap-2 mb-3">
              <span class="flex-1 bg-white/5 rounded-lg px-2 py-1.5 text-center"><span class="block text-sm font-black text-white">{{students_total}}</span><span class="text-[10px] uppercase tracking-wide text-slate-400">{{students_label}}</span></span>
              <span class="flex-1 bg-white/5 rounded-lg px-2 py-1.5 text-center"><span class="block text-sm font-black text-white">{{staff_total}}</span><span class="text-[10px] uppercase tracking-wide text-slate-400">{{staff_label}}</span></span>
            </div>{{/students_total}}
            <p class="text-xs text-slate-400 leading-relaxed">{{address}}</p>
            {{#chairman}}<p class="text-[11px] text-slate-500 mt-1.5">{{chairman_label}}: {{chairman}}</p>{{/chairman}}
            <div class="mt-auto pt-4 border-t border-white/10 flex items-center justify-between gap-3">
              <div class="flex items-center gap-2 text-slate-400">
                {{#social_youtube}}<a href="{{social_youtube}}" target="_blank" rel="noopener" aria-label="YouTube" class="hover:text-white transition"><svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.5 12 3.5 12 3.5s-7.5 0-9.4.6A3 3 0 0 0 .5 6.2 31 31 0 0 0 0 12a31 31 0 0 0 .5 5.8 3 3 0 0 0 2.1 2.1c1.9.6 9.4.6 9.4.6s7.5 0 9.4-.6a3 3 0 0 0 2.1-2.1A31 31 0 0 0 24 12a31 31 0 0 0-.5-5.8zM9.6 15.6V8.4l6.2 3.6-6.2 3.6z"/></svg></a>{{/social_youtube}}
                {{#social_facebook}}<a href="{{social_facebook}}" target="_blank" rel="noopener" aria-label="Facebook" class="hover:text-white transition"><svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M24 12a12 12 0 1 0-13.9 11.9v-8.4H7v-3.5h3.1V9.4c0-3 1.8-4.7 4.6-4.7 1.3 0 2.7.2 2.7.2v3h-1.5c-1.5 0-2 .9-2 1.9v2.2h3.4l-.5 3.5h-2.9v8.4A12 12 0 0 0 24 12z"/></svg></a>{{/social_facebook}}
                {{#social_instagram}}<a href="{{social_instagram}}" target="_blank" rel="noopener" aria-label="Instagram" class="hover:text-white transition"><svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2.2c3.2 0 3.6 0 4.9.1 1.2.1 1.8.3 2.2.4.6.2 1 .5 1.4.9.4.4.7.8.9 1.4.1.4.3 1 .4 2.2.1 1.3.1 1.7.1 4.9s0 3.6-.1 4.9c-.1 1.2-.3 1.8-.4 2.2-.2.6-.5 1-.9 1.4-.4.4-.8.7-1.4.9-.4.1-1 .3-2.2.4-1.3.1-1.7.1-4.9.1s-3.6 0-4.9-.1c-1.2-.1-1.8-.3-2.2-.4-.6-.2-1-.5-1.4-.9-.4-.4-.7-.8-.9-1.4-.1-.4-.3-1-.4-2.2-.1-1.3-.1-1.7-.1-4.9s0-3.6.1-4.9c.1-1.2.3-1.8.4-2.2.2-.6.5-1 .9-1.4.4-.4.8-.7 1.4-.9.4-.1 1-.3 2.2-.4 1.3-.1 1.7-.1 4.9-.1zm0 5.6a4.2 4.2 0 1 0 0 8.4 4.2 4.2 0 0 0 0-8.4zm0 6.9a2.7 2.7 0 1 1 0-5.4 2.7 2.7 0 0 1 0 5.4zm5.3-7.1a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"/></svg></a>{{/social_instagram}}
                {{#phone}}<a href="tel:{{phone}}" aria-label="Call" class="hover:text-white transition"><svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M6.6 10.8a15.5 15.5 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.2 11 11 0 0 0 3.5.6 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1 11 11 0 0 0 .6 3.5 1 1 0 0 1-.2 1l-2.3 2.3z"/></svg></a>{{/phone}}
              </div>
              <a href="{{donate_url}}" target="_blank" rel="noopener" class="shrink-0 inline-flex items-center bg-amber-400 text-slate-950 text-xs font-black rounded-xl px-4 min-h-11 hover:bg-amber-300 active:scale-[0.98] transition shadow-lg">{{donate_label}}</a>
            </div>
          </div>
        </article>"""

def _render_school_card(fields):
    html = re.sub(r"\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}",
                  lambda m: m.group(2) if fields.get(m.group(1)) not in (None, "", False) else "",
                  SCHOOL_CARD_TEMPLATE, flags=re.S)
    html = re.sub(r"\{\{(\w+)\}\}",
                  lambda m: "" if fields.get(m.group(1)) is None else str(fields.get(m.group(1))),
                  html)
    return html

def render_school_cards(lang):
    with open(schools_data_path, encoding="utf-8") as f:
        data = json.load(f)
    meta = data["_meta"]
    lab = SCHOOL_LABELS[lang]
    cards = []
    for s in data["schools"]:
        photo_exists = os.path.exists(os.path.join(assets_src, "schools", s["slug"] + ".webp"))
        cards.append(_render_school_card({
            "name": s.get("name_" + lang),
            "place": s.get("place_" + lang),
            "address": s.get("address_" + lang),
            "year_started": s.get("year_started"),
            "students_total": s.get("students", {}).get("total"),
            "staff_total": s.get("staff", {}).get("total"),
            "phone": s.get("phone"),
            "chairman": s.get("chairman_" + lang),
            "photo": s.get("photo"),
            "has_photo": "1" if photo_exists else None,
            "social_youtube": s.get("social", {}).get("youtube"),
            "social_facebook": s.get("social", {}).get("facebook"),
            "social_instagram": s.get("social", {}).get("instagram"),
            "donate_url": meta["shared_stripe_link"] + "?client_reference_id=" + s["donate"]["ref"],
            "est_label": lab["est"], "students_label": lab["students"], "staff_label": lab["staff"],
            "chairman_label": lab["chairman"], "donate_label": lab["donate"],
        }))
    print(f"  -> Generated {len(cards)} school cards ({lang})")
    return "\n".join(cards)

school_marker = re.compile(r"<!--#\s*school-cards\s+lang=[\"'](\w+)[\"']\s*-->")

print("🚀 Starting Production Build Pipeline...")
print(f"📄 Code Directory:   {source_dir}")
print(f"🖼️ Media Directory:  {assets_src}")
print(f"📦 Output Target:     {build_dir}\n")

# 1. Compile English Page from its subfolder path
print("Compiling en/index.html...")
en_html = process_file(os.path.join(source_dir, "en", "index.html"))
with open(os.path.join(build_dir, "en", "index.html"), "w", encoding="utf-8") as f:
    f.write(en_html)

# 2. Compile Tamil Page from its subfolder path
print("\nCompiling ta/index.html...")
ta_html = process_file(os.path.join(source_dir, "ta", "index.html"))
with open(os.path.join(build_dir, "ta", "index.html"), "w", encoding="utf-8") as f:
    f.write(ta_html)

# 3. Compile English Gallery page
print("\nCompiling en/gallery.html...")
en_gallery_html = process_file(os.path.join(source_dir, "en", "gallery.html"))
with open(os.path.join(build_dir, "en", "gallery.html"), "w", encoding="utf-8") as f:
    f.write(en_gallery_html)

# 4. Compile Tamil Gallery page
print("\nCompiling ta/gallery.html...")
ta_gallery_html = process_file(os.path.join(source_dir, "ta", "gallery.html"))
with open(os.path.join(build_dir, "ta", "gallery.html"), "w", encoding="utf-8") as f:
    f.write(ta_gallery_html)

# 4b. Compile legal pages (Privacy Policy + Terms of Service) for both languages.
#     Same English legal text in en/ and ta/; the ta/ versions carry Tamil chrome.
legal_pages = [
    ("en", "privacy.html"),
    ("en", "terms.html"),
    ("ta", "privacy.html"),
    ("ta", "terms.html"),
]
for lang_dir, page in legal_pages:
    print(f"\nCompiling {lang_dir}/{page}...")
    compiled = process_file(os.path.join(source_dir, lang_dir, page))
    with open(os.path.join(build_dir, lang_dir, page), "w", encoding="utf-8") as f:
        f.write(compiled)

# 4c. Compile Schools page (both languages). Cards are generated from
#     html/data/schools.json and injected at the <!--#school-cards--> marker
#     after SSI includes are resolved.
for lang_dir in ("en", "ta"):
    print(f"\nCompiling {lang_dir}/schools.html...")
    compiled = process_file(os.path.join(source_dir, lang_dir, "schools.html"))
    compiled = school_marker.sub(lambda m: render_school_cards(m.group(1)), compiled)
    with open(os.path.join(build_dir, lang_dir, "schools.html"), "w", encoding="utf-8") as f:
        f.write(compiled)

# 5. Create Root Redirect File
root_index_content = """<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0; url=/en/">
    <link rel="icon" href="/assets/favicon.ico" sizes="any">
    <script type="text/javascript">
        window.location.href = "/en/"
    </script>
    <title>International Educational Foundation</title>
</head>
<body>
    <p>Redirecting to the main page... If you are not forwarded, <a href="/en/">click here</a>.</p>
</body>
</html>
"""
with open(os.path.join(build_dir, "index.html"), "w", encoding="utf-8") as f:
    f.write(root_index_content)

# 6. Pull media assets from the 1TB HDD volume
if os.path.exists(assets_src):
    print(f"\n📦 Copying production media assets from HDD vault ({assets_src})...")
    shutil.copytree(assets_src, assets_dst)
    print(f"✅ Successfully compiled {len(os.listdir(assets_dst))} media assets.")
    # Also place favicon.ico at the site root so bare /favicon.ico requests resolve.
    root_favicon = os.path.join(assets_src, "favicon.ico")
    if os.path.exists(root_favicon):
        shutil.copy(root_favicon, os.path.join(build_dir, "favicon.ico"))
        print("✅ Placed favicon.ico at site root.")
else:
    print(f"\n⚠️  Media directory not found at {assets_src}")
    print(f"   Skipping assets — existing Cloudflare CDN assets will be preserved.")
    print(f"   (Run deploy.sh locally to do a full asset deploy)")

print(f"\n🎉 Build Complete! Clean production distribution compiled at: {build_dir}")

