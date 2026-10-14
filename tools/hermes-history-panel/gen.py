# -*- coding: utf-8 -*-
"""pdf2zh 翻译历史页生成器（Hermes）。root 由调用方传入：
    容器内 = /app/pdf2zh_files ；宿主机 = /home/ethan/pdf2zh/files
"""
import datetime as _dt, glob as _g, html as _h, os as _o, urllib.parse as _u

FILE_URL = "/gradio_api/file="          # Gradio 已有路由；该目录本就在 allowed_paths 内
# 删除走同源相对地址 /p2z-del（由 pdf2zh 补丁在 7860 上注册）


def _kind(name):
    n = name.lower()
    if "dual" in n:
        return ("中英对照", "#8ab4ff")
    if "mono" in n:
        return ("纯中文", "#7ee0a8")
    return ("原文", "#c9a86a")


def _collect(root):
    files = [_f for _f in _g.glob(_o.path.join(root, "**", "*.pdf"), recursive=True)
             if "/_hist/" not in _f.replace(_o.sep, "/")]
    groups = {}
    for f in files:
        groups.setdefault(_o.path.dirname(f), []).append(f)
    ordered = sorted(groups.items(), key=lambda kv: max(_o.path.getmtime(x) for x in kv[1]), reverse=True)
    return ordered, len(files)


def build_history_html(root):
    ordered, total = _collect(root)
    cards = []
    for _, files in ordered:
        files = sorted(files, key=lambda x: (("dual" not in x.lower()), ("mono" not in x.lower())))
        src = max(files, key=lambda x: len(_o.path.basename(x)))
        title = _o.path.basename(src)
        for suf in (".no_watermark.zh-CN.dual.pdf", ".no_watermark.zh-CN.mono.pdf", ".dual.pdf", ".mono.pdf"):
            if title.endswith(suf):
                title = title[: -len(suf)] + ".pdf"
        rows = []
        for f in files:
            lbl, col = _kind(_o.path.basename(f))
            rel = _o.path.relpath(f, root)
            mt = _dt.datetime.fromtimestamp(_o.path.getmtime(f)).strftime("%Y-%m-%d %H:%M")
            sz = _o.path.getsize(f) / 1048576.0
            rows.append(
                '<li><span class="tag" style="color:%s;border-color:%s">%s</span>'
                '<a class="fl" href="%s%s" target="_blank" rel="noopener">%s</a>'
                '<span class="meta">%s &middot; %.1f MB</span>'
                '<form class="delf" method="post" action="/p2z-del">'
                '<input type="hidden" name="f" value="%s">'
                '<button type="submit" title="删除该文件">删除</button></form></li>'
                % (col, col, lbl, FILE_URL, _u.quote(f), _h.escape(_o.path.basename(f)), mt, sz,
                   _h.escape(rel)))
        cards.append('<section class="card"><h2>%s</h2><ul>%s</ul></section>'
                     % (_h.escape(title), "".join(rows) or "<li>（无文件）</li>"))
    page = """<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>PDF 翻译历史</title><style>
:root{color-scheme:dark}*{box-sizing:border-box}
body{margin:0;background:#0f1115;color:#e8ecf3;font-family:system-ui,-apple-system,"Noto Sans CJK SC","PingFang SC","Microsoft YaHei",sans-serif}
header{position:sticky;top:0;z-index:9;display:flex;align-items:center;gap:12px;flex-wrap:wrap;
 padding:13px 16px;background:rgba(26,29,36,.96);backdrop-filter:blur(6px);border-bottom:1px solid #23262e}
header h1{font-size:17px;margin:0;font-weight:600}
header a.back{color:#8ab4ff;text-decoration:none;font-size:14px}
.count{color:#8b93a1;font-size:12px;margin-left:auto}
.wrap{max-width:900px;margin:0 auto;padding:14px 12px 60px}
.card{background:#161922;border:1px solid #232734;border-radius:12px;padding:13px 15px;margin:13px 0}
.card h2{font-size:15px;margin:0 0 9px;font-weight:600;line-height:1.45;word-break:break-word;color:#fff}
.card ul{list-style:none;margin:0;padding:0}
.card li{display:flex;flex-wrap:wrap;align-items:center;gap:9px;padding:10px 0;border-top:1px solid #222634}
.card li:first-child{border-top:0}
.tag{font-size:12px;border:1px solid;border-radius:999px;padding:1px 9px;white-space:nowrap}
.fl{color:#9ecbff;text-decoration:none;font-size:14px;word-break:break-all;flex:1 1 55%}
.fl:hover{text-decoration:underline}
.meta{color:#8b93a1;font-size:12px;white-space:nowrap}
.delf{margin:0}
.delf button{background:#2a1f22;color:#ff9d9d;border:1px solid #4a2b30;border-radius:8px;
 padding:5px 10px;font-size:12px;cursor:pointer}
.delf button:hover{background:#3a2429;color:#ffc0c0}
.empty{color:#8b93a1;padding:40px 0;text-align:center}
footer{color:#6b7280;font-size:12px;text-align:center;padding:12px 0 0}
</style></head><body>
<header><a class="back" href="/">&#8592; 返回翻译</a><h1>PDF 翻译历史</h1>
<span class="count">__N__ 次翻译 / __TOTAL__ 个文件</span></header>
<div class="wrap">__CARDS__<footer>本页在打开翻译主页时自动生成；新翻译完成后回主页刷新一次即可</footer></div>
<script>
(function(){
  document.querySelectorAll('form.delf').forEach(function(f){
    f.addEventListener('submit', function(e){
      if(!confirm('确定删除该文件？此操作不可恢复。')){ e.preventDefault(); }
    });
  });
})();
</script></body></html>"""
    return (page.replace("__N__", str(len(ordered)))
                .replace("__TOTAL__", str(total))
                .replace("__CARDS__", "".join(cards) or '<div class="empty">暂无翻译结果</div>')
                )


def write_history_page(root):
    """生成 _hist/index.html，返回 (路径, 次数, 文件数)"""
    outdir = _o.path.join(root, "_hist")
    _o.makedirs(outdir, exist_ok=True)
    p = _o.path.join(outdir, "index.html")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(build_history_html(root))
    ordered, total = _collect(root)
    return p, len(ordered), total


def entry_html(root, page_path):
    """页面顶部入口链接（指向通过 Gradio 文件路由提供的独立页）"""
    ordered_, total = _collect(root)
    n = len(ordered_)
    return ('<div style="margin:6px 0 12px;font-family:system-ui,-apple-system,sans-serif">'
            '<a href="/p2z-hist" target="_blank" rel="noopener" '
            'style="display:inline-block;padding:10px 16px;border-radius:10px;background:#20242e;'
            'color:#ffffff;text-decoration:none;font-size:15px;font-weight:500">'
            '翻译历史（%d 次翻译 / %d 个文件）· 打开独立页面</a></div>' % (n, total))


if __name__ == "__main__":
    import sys
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.realpath("pdf2zh_files")
    p, n, total = write_history_page(root)
    print("生成:", p, "| 次数", n, "| 文件", total)
