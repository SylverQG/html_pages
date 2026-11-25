#!/usr/bin/env python3
"""部署前给仓库内所有 HTML 页面右上角注入"返回主页"三角按钮。

在 GitHub Actions 里、上传产物之前运行：
    python3 _generator/inject_home_button.py

- 遍历仓库内所有 .html，跳过 index.html、.git 和 _generator
- 链接按页面所在目录自动计算到首页的相对路径（如 docs/xxx.html -> ../index.html）
- 幂等：已注入过（含 MARKER）的文件直接跳过

只在 CI 产物里生效，仓库源文件不受影响。
"""
import os
import re

ROOT = os.path.abspath(".")
EXCLUDE_FILES = {"index.html"}
EXCLUDE_DIRS = {".git", "_generator"}
MARKER = 'id="home-corner"'

# 配色与作品集首页一致（--bg #0b1020 / --accent #3b82f6）
SNIPPET = """<style>
#home-corner {
  position: fixed;
  top: 0;
  right: 0;
  width: 96px;
  height: 96px;
  display: block;
  background: linear-gradient(225deg, #1d4ed8, #0b1020 85%);
  clip-path: polygon(0 0, 100% 0, 100% 100%);
  z-index: 2147483647;
  opacity: .92;
  cursor: pointer;
  transform-origin: top right;
  transition: transform .22s ease, opacity .22s ease, filter .22s ease;
}
#home-corner:hover,
#home-corner:focus-visible {
  transform: scale(1.15);
  opacity: 1;
  filter: brightness(1.4);
}
#home-corner:focus-visible {
  outline: none;
}
#home-corner svg {
  position: absolute;
  left: 66.7%;   /* 三角形可视区域的重心 */
  top: 33.3%;
  transform: translate(-50%, -50%);
  width: 28px;
  height: 28px;
  color: #fff;
  filter: drop-shadow(0 1px 2px rgba(0,0,0,.4));
}
</style>
<a id="home-corner" href="__HREF__" title="返回主页" aria-label="返回主页">
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
       stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
    <polyline points="9 22 9 12 15 12 15 22"/>
  </svg>
</a>
"""


def inject(filepath: str, href: str) -> bool:
    with open(filepath, encoding="utf-8", errors="ignore") as f:
        content = f.read()

    if MARKER in content:
        return False  # 已注入过

    snippet = SNIPPET.replace("__HREF__", href)
    new_content, n = re.subn(r"</body\s*>", snippet + "</body>", content,
                             count=1, flags=re.IGNORECASE)
    if n == 0:  # 没有 </body> 就整个追加到末尾
        new_content = content + "\n" + snippet

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
    return True


def main():
    injected, skipped = [], []

    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for f in filenames:
            if not f.endswith(".html") or f in EXCLUDE_FILES:
                continue
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
            href = os.path.relpath("index.html", os.path.dirname(rel) or ".").replace(os.sep, "/")
            (injected if inject(full, href) else skipped).append(rel)

    for rel in injected:
        print(f"  💉 {rel}")
    print(f"✅ 注入 {len(injected)} 个文件，跳过 {len(skipped)} 个（已含按钮）")


if __name__ == "__main__":
    main()
