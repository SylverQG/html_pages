#!/usr/bin/env python3
import os, re, html as htmllib
from datetime import datetime, timezone

ROOT = os.path.abspath(".")
OUT = os.path.join(ROOT, "index.html")
EXCLUDE = {"index.html"}

def get_title(filepath):
    """尝试读取 HTML 文件的 <title> 标签"""
    try:
        with open(filepath, encoding="utf-8", errors="ignore") as f:
            content = f.read(4096)
        m = re.search(r"<title[^>]*>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
        if m:
            title = m.group(1).strip()
            if title:
                return title
    except Exception:
        pass
    return None

pages = []

for dirpath, dirnames, filenames in os.walk(ROOT):
    # 跳过
    if "/.git" in dirpath or "\\.git" in dirpath:
        continue
    if os.path.basename(dirpath) == "_generator":
        continue

    for f in filenames:
        if not f.endswith(".html"):
            continue
        full = os.path.join(dirpath, f)
        rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
        if rel in EXCLUDE:
            continue

        title = get_title(full)
        display_name = title if title else rel[:-5]
        dir_name = os.path.dirname(rel).replace("\\", "/")

        pages.append({
            "name": display_name,
            "path": rel,
            "dir": dir_name,
            "search_text": (display_name + " " + rel).lower(),
        })

# 按目录分组
pages.sort(key=lambda p: (p["dir"], p["name"].lower()))
groups = {}
for p in pages:
    d = p["dir"] or "其他"
    groups.setdefault(d, []).append(p)

data = {
    "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    "count": len(pages),
    "groups": groups,
}

tmpl_path = os.path.join(ROOT, "_generator", "template.html")
with open(tmpl_path, encoding="utf-8") as f:
    template = f.read()

# 渲染分组
sections = ""
for group_name, items in groups.items():
    section_id = htmllib.escape(group_name.replace("/", "-").replace(" ", "-"))
    sections += f'''
    <section class="group" data-group="{htmllib.escape(group_name.lower())}">
      <h2 class="group-title">{htmllib.escape(group_name)} <span class="group-count">{len(items)}</span></h2>
      <div class="grid">
    '''
    for p in items:
        sections += f'''
        <a class="card" href="{htmllib.escape(p['path'])}" data-search="{htmllib.escape(p['search_text'])}">
          <div class="card-icon">📄</div>
          <div class="card-body">
            <div class="card-title">{htmllib.escape(p['name'])}</div>
            <div class="card-path">{htmllib.escape(p['path'])}</div>
          </div>
        </a>
        '''
    sections += '''
      </div>
    </section>
    '''

if not sections:
    sections = '<p class="empty">仓库里还没有其他 HTML 文件 🤷</p>'

ctx = {
    "generated_at": data["generated_at"],
    "count": str(data["count"]),
    "sections": sections,
}

for k, v in ctx.items():
    template = template.replace("{{ " + k + " }}", v)

with open(OUT, "w", encoding="utf-8") as f:
    f.write(template)

print(f"✅ generated index.html with {len(pages)} html files in {len(groups)} groups")