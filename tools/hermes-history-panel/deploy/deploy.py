#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v6：删除功能完全做在 7860 上
- gen.py：删除表单改为同源相对地址 /p2z-del（页面就在 7860，无需任何其它端口）
- 补丁：包一层 demo.launch（**原样调用原 launch**，不改变启动方式），另起守护线程在该应用的路由表最前面插入 /p2z-del
- 本地先把两个函数都自测通过，再部署
"""
import ast, os, base64, time, subprocess
import os
import paramiko

PW = os.environ.get("P2Z_PW") or __import__("getpass").getpass("ethan@192.168.1.232 密码: ")
C = "infallible_hawking"
IMG = "awwaawwa/pdfmathtranslate-next"
SP = "/usr/local/lib/python3.13/site-packages/pdf2zh_next/gui.py"
PD = "/home/ethan/pdf2zh/patch"
FILES_ROOT = "/home/ethan/pdf2zh/files"
BASE = f'-v /home/ethan/pdf2zh/config:/root/.config/pdf2zh -v {FILES_ROOT}:/app/pdf2zh_files'

# ── ① 修 gen.py：修 entry_html 解包 bug + 删除表单改同源 ──
g = open('/home/agent/p2z-hist/gen.py', encoding='utf-8').read()
g = g.replace('    _, n, total = _collect(root)\n',
              '    ordered_, total = _collect(root)\n    n = len(ordered_)\n')
g = g.replace('<form class="delf" method="post" action="">', '<form class="delf" method="post" action="/p2z-del">')
# 去掉跨端口 JS（同源就不需要了）
i0 = g.find('<script>')
i1 = g.find('</script>', i0)
if i0 != -1 and i1 != -1:
    g = g[:i0] + ('<script>\n(function(){\n'
                  "  document.querySelectorAll('form.delf').forEach(function(f){\n"
                  "    f.addEventListener('submit', function(e){\n"
                  "      if(!confirm('确定删除该文件？此操作不可恢复。')){ e.preventDefault(); }\n"
                  "    });\n  });\n})();\n") + g[i1:]
g = g.replace('DEL_URL_PORT = 8088                     # 删除接口所在端口（复用已有的 apk-server）\n',
              '# 删除走同源相对地址 /p2z-del（由 pdf2zh 补丁在 7860 上注册）\n')
open('/home/agent/p2z-hist/gen.py', 'w', encoding='utf-8').write(g)
ast.parse(g)
print("① gen.py 已修:", 'action="/p2z-del"' in g, "| 无 8088 引用:", '8088' not in g)

# 本地自测两个函数（这次不漏 entry_html）
test_root = '/home/agent/_hist_test4'
os.makedirs(test_root + '/abc', exist_ok=True)
open(test_root + '/abc/Paper X.no_watermark.zh-CN.dual.pdf', 'wb').write(b'%PDF' + b'x' * 90000)
ns = {'__name__': 'gen_test'}
exec(compile(g, 'gen.py', 'exec'), ns)
p, n, total = ns['write_history_page'](test_root)
ent = ns['entry_html'](test_root, p)
print("   自测: 页", os.path.getsize(p), "字节 | 次数", n, "| 文件", total)
print("   入口含独立页链接:", 'gradio_api/file=' in ent, "| 删除表单同源:", 'action="/p2z-del"' in open(p, encoding='utf-8').read())

# ── ② 生成补丁 v6 ──
gen_core = g.split('if __name__ == "__main__":')[0].rstrip() + '\n'
INSTALL = r'''

# ── 7860 原生删除接口安装器（只加路由，不改启动方式）──
def _hermes_install_del_route() -> None:
    import threading as _th, time as _tm

    def worker():
        from starlette.routing import Route as _R
        from starlette.responses import HTMLResponse as _HR
        for _ in range(180):
            _tm.sleep(1)
            app = getattr(demo, "app", None)
            routes = getattr(getattr(app, "router", None), "routes", None)
            if not routes:
                continue
            if any(getattr(_r, "path", "") == "/p2z-del" for _r in routes):
                return
            async def _p2z_del(request):
                import os as _os2, urllib.parse as _u2
                try:
                    form = await request.form()
                    rel = str(form.get("f") or "")
                    root = _os2.path.realpath("pdf2zh_files")
                    full = _os2.path.realpath(_os2.path.join(root, rel))
                    ok = (rel and full.startswith(root + _os2.sep)
                          and "/_hist/" not in full and full.lower().endswith(".pdf"))
                    if not ok:
                        return _HR(_hermes_result("拒绝删除", "路径不合法（只允许删除翻译目录内的 PDF）。"), status_code=400)
                    name = _os2.path.basename(full)
                    if not _os2.path.exists(full):
                        return _HR(_hermes_result("文件不存在", "可能已被删除。", name))
                    _os2.remove(full)
                    _pp, _n, _t = write_history_page(root)
                    print("[hermes] 已删除 %s → 剩 %d 次翻译 / %d 个文件" % (full, _n, _t), flush=True)
                    return _HR(_hermes_result("已删除", "<b>%s</b>" % name,
                                              extra="当前共 %d 次翻译 / %d 个文件" % (_n, _t)))
                except Exception as _e:
                    return _HR(_hermes_result("删除失败", str(_e)[:200]), status_code=500)

            async def _p2z_hist(request):
                import os as _os3
                try:
                    root = _os3.path.realpath("pdf2zh_files")
                    write_history_page(root)
                    with open(_o.path.join(root, "_hist", "index.html"), encoding="utf-8") as _f:
                        return _HR(_f.read())
                except Exception as _e:
                    return _HR("生成失败: %s" % str(_e)[:200], status_code=500)

            routes.insert(0, _R("/p2z-hist", _p2z_hist, methods=["GET"]))
            routes.insert(0, _R("/p2z-del", _p2z_del, methods=["POST"]))
            print("[hermes] /p2z-del 已挂在 7860", flush=True)
            return
    _th.Thread(target=worker, daemon=True).start()


def _hermes_result(title, body, extra=""):
    hist = "/p2z-hist"   # 同源，每次打开都重新生成
    return ("<!doctype html><html lang=zh><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'><title>%s</title><style>"
            "body{margin:0;background:#0f1115;color:#e8ecf3;font-family:system-ui,-apple-system,sans-serif;"
            "display:flex;min-height:100vh;align-items:center;justify-content:center}"
            ".b{max-width:560px;padding:28px 24px;background:#161922;border:1px solid #232734;border-radius:14px;text-align:center}"
            "h1{font-size:19px;margin:0 0 12px}p{color:#9aa3b2;font-size:14px;line-height:1.6;margin:8px 0;word-break:break-all}"
            "a{display:inline-block;margin:14px 8px 0;padding:10px 16px;border-radius:9px;text-decoration:none;font-size:14px}"
            ".p{background:#2b6cff;color:#fff}.s{background:#20242e;color:#e8ecf3}</style></head><body><div class=b>"
            "<h1>%s</h1>%s<p>%s</p><a class=p href='%s'>重新打开历史页</a><a class=s href='/'>返回翻译主页</a>"
            "</div></body></html>" % (title, title, extra, body, hist))

'''

BLOCK = ('\n# ───────── Hermes 补丁（安全版）：独立历史页（7860 内删除）+ 页面入口 ─────────\n'
         + gen_core + INSTALL +
         '\n_HERMES_ROOT = __import__("os").path.realpath("pdf2zh_files")\n'
         '_HERMES_HIST_PAGE, _H, _T = write_history_page(_HERMES_ROOT)\n'
         '_HERMES_HIST_HTML = entry_html(_HERMES_ROOT, _HERMES_HIST_PAGE)\n'
         '# ───────── 补丁结束 ─────────\n')
ENTRY = ("    gr.HTML(_HERMES_HIST_HTML)  # hermes-hist-entry\n"
         "    _hermes_orig_launch = demo.launch\n"
         "    def _hermes_launch(*a, **kw):\n"
         "        _hermes_install_del_route()\n"
         "        return _hermes_orig_launch(*a, **kw)  # 原样调用；启动方式不变\n"
         "    demo.launch = _hermes_launch\n")
src = open('/home/agent/gui_sp.py', encoding='utf-8').read()
i = src.index('if not config_fake_pdf_path.exists():')
patched = src[:i] + BLOCK + '\n' + src[i:]
j = patched.index(') as demo:\n') + len(') as demo:\n')
patched = patched[:j] + ENTRY + patched[j:]
ast.parse(patched)
open('/home/agent/gui_patched_v6.py', 'w', encoding='utf-8').write(patched)
print("② 补丁 v6:", len(patched), "字节 | 语法 OK")

# ── ③ 部署 ──
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect("192.168.1.232", username="ethan", password=PW, timeout=20)


def sh(cmd, t=240):
    _i, o, e = cli.exec_command(cmd, timeout=t)
    return (o.read().decode() + e.read().decode()).strip()


def push(text, dest):
    b64 = base64.b64encode(text.encode('utf-8')).decode()
    sh("rm -f /tmp/_v6_*")
    for k in range(0, len(b64), 3000):
        sh(f"printf %s '{b64[k:k+3000]}' > /tmp/_v6_{k//3000:04d}")
    return sh(f'cat /tmp/_v6_* > /tmp/_v6.b64 && base64 -d /tmp/_v6.b64 > {dest} && rm -f /tmp/_v6_* /tmp/_v6.b64 && wc -c {dest}')


print("\n③ 推送:", push(patched, f'{PD}/gui.py'), "| 片段:", push(BLOCK, f'{PD}/_entry.py.snippet'))
print(sh(f'docker rm -f {C} 2>&1 | tail -1'))
print(sh(f'docker run -d --name {C} --restart unless-stopped -p 7860:7860 {BASE} -v {PD}/gui.py:{SP} {IMG} pdf2zh --gui', t=240)[:60])
ready = False
for i in range(10):
    time.sleep(10)
    code = sh('curl -s -o /dev/null -w "%{http_code}" -m 8 http://127.0.0.1:7860/')
    print(f"   {i*10+10:3d}s HTTP={code}")
    if code in ("200", "307"):
        ready = True
        break
if not ready:
    print("   ✗ 日志:", sh(f'docker logs --tail 20 {C} 2>&1 | tail -10'))
cli.close()
subprocess.run(['bash', '-lc', 'rm -rf /home/agent/_hist_test4 /home/agent/_hist_test3; echo cleaned'], capture_output=True)
