import base64
import csv
import html
import pathlib
import re
import shutil
import subprocess


def format_inline(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    return escaped


def md_to_html(md_text: str) -> str:
    lines = md_text.splitlines()
    out = []
    in_ul = False
    table_rows = []

    def flush_table():
        nonlocal table_rows
        if not table_rows:
            return
        out.append("<table>")
        for idx, row in enumerate(table_rows):
            cells = [c.strip() for c in row.strip("|").split("|")]
            if idx == 1 and all(set(c) <= set("-: ") for c in cells):
                continue
            tag = "th" if idx == 0 else "td"
            if idx == 0:
                out.append("<thead><tr>" + "".join(f"<{tag}>{format_inline(c)}</{tag}>" for c in cells) + "</tr></thead><tbody>")
            else:
                out.append("<tr>" + "".join(f"<{tag}>{format_inline(c)}</{tag}>" for c in cells) + "</tr>")
        out.append("</tbody></table>")
        table_rows = []

    for line in lines:
        s = line.strip()
        if s.startswith("|") and s.endswith("|"):
            if in_ul:
                out.append("</ul>")
                in_ul = False
            table_rows.append(s)
            continue
        flush_table()

        if not s:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            continue

        if s == "---":
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append("<hr>")
        elif s.startswith("### "):
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append(f"<h3>{format_inline(s[4:])}</h3>")
        elif s.startswith("## "):
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append(f"<h2>{format_inline(s[3:])}</h2>")
        elif s.startswith("# "):
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append(f"<h1>{format_inline(s[2:])}</h1>")
        elif s.startswith("* ") or s.startswith("- "):
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{format_inline(s[2:])}</li>")
        elif re.match(r"^\d+\.\s+", s):
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{format_inline(re.sub(r'^\d+\.\s+', '', s))}</li>")
        else:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append(f"<p>{format_inline(s)}</p>")

    flush_table()
    if in_ul:
        out.append("</ul>")
    return "\n".join(out)


def build_feature_catalog_html(csv_path: pathlib.Path) -> str:
    if not csv_path.exists():
        return ""
    rows_html = []
    with csv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            fname = html.escape(row.get("feature_name", ""))
            dtype = html.escape(row.get("dtype", ""))
            missing = html.escape(row.get("missing_count", "0"))
            rows_html.append(
                f"<tr><td>{i}</td><td><code>{fname}</code></td><td><code>{dtype}</code></td><td>{missing}</td></tr>"
            )
    return (
        "<h2>۶. فهرست کامل ویژگی‌های مهندسی‌شده (۳۰ ویژگی سطح نقد)</h2>"
        "<p>جدول زیر مشخصات کامل ماتریس ویژگی خروجی فاز دوم (<code>14,792 × 30</code>) را نمایش می‌دهد:</p>"
        "<table><thead><tr><th>ردیف</th><th>نام ویژگی</th><th>نوع داده</th><th>تعداد گمشده</th></tr></thead>"
        f"<tbody>{''.join(rows_html)}</tbody></table>"
    )


def build_figures_html(root: pathlib.Path) -> str:
    figures = [
        ("figures/phase2/clustering_k_selection.png", "شکل ۱: انتخاب تعداد خوشه بهینه (k=5) بر اساس Inertia و Silhouette Score"),
        ("figures/phase2/umap_clusters_and_ratings.png", "شکل ۲: نقشه معنایی ۵ خوشه در فضای UMAP و میانگین امتیاز مشتریان در هر جنبه"),
        ("figures/phase2/cluster_stability_ari.png", "شکل ۳: ارزیابی پایداری خوشه‌ها با شاخص ARI در برابر تغییر Seed و زیرنمونه ۸۰٪"),
    ]
    blocks = ["<h2>۷. پیوست مصورسازی‌های کلیدی فاز دوم</h2>"]
    for rel_path, caption in figures:
        img_file = root / rel_path
        if img_file.exists():
            encoded = base64.b64encode(img_file.read_bytes()).decode("ascii")
            blocks.append(
                f'<div class="fig-box"><img src="data:image/png;base64,{encoded}" alt="{caption}">'
                f'<div class="caption">{caption}</div></div>'
            )
    return "\n".join(blocks)


def find_browser() -> str:
    candidates = [
        shutil.which("msedge"),
        shutil.which("chrome"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for path in candidates:
        if path and pathlib.Path(path).exists():
            return str(path)
    raise FileNotFoundError("مرورگر Edge یا Chrome برای تولید PDF پیدا نشد.")


def main():
    root = pathlib.Path(__file__).resolve().parent.parent
    md_path = root / "reports" / "phase2" / "phase2.md"
    html_path = root / "reports" / "phase2" / "_temp_phase2.html"
    pdf_path = root / "reports" / "phase2" / "phase2.pdf"
    catalog_path = root / "data" / "interim" / "phase2_feature_catalog.csv"

    raw_md = md_path.read_text(encoding="utf-8")
    clean_md = re.sub(r"\s*\[\s*cite\s*:[^\]]*\]", "", raw_md)
    md_path.write_text(clean_md, encoding="utf-8")

    body_html = md_to_html(clean_md)
    catalog_html = build_feature_catalog_html(catalog_path)
    figures_html = build_figures_html(root)

    full_html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<style>
  @page {{ size: A4; margin: 16mm 15mm; }}
  body {{
    font-family: "Segoe UI", Tahoma, sans-serif;
    line-height: 1.85;
    color: #1e293b;
    font-size: 10.2pt;
    text-align: justify;
  }}
  h1 {{
    font-size: 15pt;
    color: #0f172a;
    background: #eff6ff;
    border-right: 5px solid #1d4ed8;
    padding: 12px 15px;
    border-radius: 4px;
    margin-bottom: 16px;
  }}
  h2 {{
    font-size: 12.2pt;
    color: #1e3a8a;
    border-bottom: 2px solid #cbd5e1;
    padding-bottom: 4px;
    margin-top: 22px;
    page-break-after: avoid;
  }}
  h3 {{
    font-size: 10.8pt;
    color: #334155;
    margin-top: 14px;
    page-break-after: avoid;
  }}
  p {{ margin: 8px 0; }}
  ul {{ padding-right: 22px; margin: 8px 0; }}
  li {{ margin-bottom: 5px; }}
  table {{
    border-collapse: collapse;
    width: 100%;
    margin: 14px 0;
    font-size: 8.8pt;
    page-break-inside: avoid;
  }}
  th, td {{
    border: 1px solid #cbd5e1;
    padding: 6px 8px;
    text-align: right;
    vertical-align: middle;
  }}
  th {{
    background-color: #1e3a8a;
    color: #ffffff;
    font-weight: bold;
  }}
  tr:nth-child(even) {{ background-color: #f8fafc; }}
  code {{
    font-family: Consolas, "Courier New", monospace;
    background: #f1f5f9;
    color: #b91c1c;
    padding: 1px 4px;
    border-radius: 3px;
    font-size: 8.8pt;
    direction: ltr;
    unicode-bidi: embed;
    display: inline-block;
  }}
  hr {{ border: none; border-top: 1px solid #e2e8f0; margin: 14px 0; }}
  .fig-box {{
    text-align: center;
    margin: 16px 0;
    padding: 10px;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    page-break-inside: avoid;
  }}
  .fig-box img {{ max-width: 90%; height: auto; }}
  .caption {{ font-size: 9pt; color: #475569; margin-top: 6px; font-weight: bold; }}
</style>
</head>
<body>
{body_html}
{catalog_html}
{figures_html}
</body>
</html>"""

    html_path.write_text(full_html, encoding="utf-8")
    browser = find_browser()

    subprocess.run(
        [
            browser,
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path.resolve()}",
            html_path.resolve().as_uri(),
        ],
        check=True,
    )

    if html_path.exists():
        html_path.unlink()

    print(f"SUCCESS: PDF generated at {pdf_path} ({pdf_path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()