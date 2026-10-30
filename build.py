#!/usr/bin/env python3
"""构建脚本：读取模板 + 语言包，生成多语言静态 HTML"""
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE_DIR, "template.html")
I18N_DIR = os.path.join(BASE_DIR, "i18n")
OUTPUT_DIR = os.path.join(BASE_DIR, "public")

LANG_FILES = {
    "zh": "zh.json",
    "en": "en.json",
    "ja": "ja.json",
    "ko": "ko.json",
}

LANG_SELECT_ATTR = {
    "zh": 'selected',
    "en": 'selected',
    "ja": 'selected',
    "ko": 'selected',
}

OG_LOCALE = {
    "zh": "zh_CN",
    "en": "en_US",
    "ja": "ja_JP",
    "ko": "ko_KR",
}

# TODO: 部署到 Cloudflare Pages 后，这里改成你的实际域名
# 例如: SITE_DOMAIN = "https://subtitle-converter.pages.dev"
SITE_DOMAIN = "https://subtitleconverter.vibe-show.com"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_hreflang(current_lang):
    tags = []
    for lang_code in LANG_FILES:
        href = f"{SITE_DOMAIN}/{lang_code}.html"
        if lang_code == "zh":
            href = f"{SITE_DOMAIN}/"
        tags.append(f'    <link rel="alternate" hreflang="{lang_code}" href="{href}">')
    tags.append(f'    <link rel="alternate" hreflang="x-default" href="{SITE_DOMAIN}/en.html">')
    return "\n".join(tags)


def build_html(lang_code, translations):
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    replacements = {}
    replacements["lang"] = translations.get("lang", lang_code)
    replacements["dir"] = translations.get("dir", "ltr")
    replacements["title"] = translations.get("title", "")
    replacements["meta_description"] = translations.get("meta_description", "")
    replacements["meta_keywords"] = translations.get("meta_keywords", "")
    replacements["og_title"] = translations.get("og_title", "")
    replacements["og_description"] = translations.get("og_description", "")
    replacements["og_locale"] = OG_LOCALE.get(lang_code, "en_US")
    replacements["canonical_url"] = (
        f"{SITE_DOMAIN}/" if lang_code == "zh" else f"{SITE_DOMAIN}/{lang_code}.html"
    )
    replacements["hreflang_tags"] = build_hreflang(lang_code)

    for other_lang in LANG_FILES:
        key = f"lang_sel_{other_lang}"
        replacements[key] = 'selected' if other_lang == lang_code else ''

    for key, value in translations.items():
        replacements[key] = value

    import re
    def replace_var(match):
        key = match.group(1)
        if key == "i18n_json":
            return json.dumps(translations, ensure_ascii=False, indent=8)
        return replacements.get(key, match.group(0))

    html = re.sub(r"\$\{(\w+)\}", replace_var, template)
    return html


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    built = []
    for lang_code, filename in LANG_FILES.items():
        json_path = os.path.join(I18N_DIR, filename)
        if not os.path.exists(json_path):
            print(f"  ⚠️  跳过 {lang_code}: {filename} 不存在")
            continue

        translations = load_json(json_path)
        html = build_html(lang_code, translations)

        out_filename = "index.html" if lang_code == "zh" else f"{lang_code}.html"
        out_path = os.path.join(OUTPUT_DIR, out_filename)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        built.append(out_filename)
        print(f"  ✅ 生成 {out_filename}  ({len(html):,} bytes)")

    # 生成 sitemap.xml
    sitemap_path = os.path.join(OUTPUT_DIR, "sitemap.xml")
    sitemap_entries = []
    for lang_code in LANG_FILES:
        url = f"{SITE_DOMAIN}/" if lang_code == "zh" else f"{SITE_DOMAIN}/{lang_code}.html"
        sitemap_entries.append(f"  <url><loc>{url}</loc><changefreq>weekly</changefreq><priority>{1.0 if lang_code == 'zh' else 0.9}</priority></url>")
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(sitemap_entries) + "\n</urlset>"
    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write(sitemap)
    built.append("sitemap.xml")
    print(f"  ✅ 生成 sitemap.xml")

    # 生成 robots.txt
    robots_path = os.path.join(OUTPUT_DIR, "robots.txt")
    robots = f"User-agent: *\nAllow: /\n\nSitemap: {SITE_DOMAIN}/sitemap.xml\n"
    with open(robots_path, "w", encoding="utf-8") as f:
        f.write(robots)
    built.append("robots.txt")
    print(f"  ✅ 生成 robots.txt")

    print(f"\n🎉 构建完成！输出目录: {OUTPUT_DIR}")
    print(f"   文件: {', '.join(built)}")
    print(f"\n💡  部署提示:")
    print(f"   1. 把 public/ 目录推送到 GitHub")
    print(f"   2. Cloudflare Pages 连接仓库，Build command 留空，Output directory 填 public")
    print(f"   3. 拿到域名后修改 build.py 里的 SITE_DOMAIN 重新构建")


if __name__ == "__main__":
    main()
