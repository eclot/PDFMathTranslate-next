

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

