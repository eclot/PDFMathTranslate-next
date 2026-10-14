#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地自测：覆盖补丁里**所有在 import 期会被执行的函数**（曾漏测 entry_html → 容器 crash-loop）"""
import os, sys, tempfile, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

tmp = tempfile.mkdtemp(prefix="p2z_selftest_")
try:
    os.makedirs(f"{tmp}/taskA")
    for n, sz in (("Paper A.pdf", 1000), ("Paper A.no_watermark.zh-CN.dual.pdf", 2000),
                  ("Paper A.no_watermark.zh-CN.mono.pdf", 1500)):
        open(f"{tmp}/taskA/{n}", "wb").write(b"%PDF" + b"x" * sz)

    src = open(f"{ROOT}/gen.py", encoding="utf-8").read().replace('"pdf2zh_files"', repr(tmp))
    ns = {"__name__": "gen"}
    exec(compile(src, "gen.py", "exec"), ns)

    # 1) 生成页
    page, n, total = ns["write_history_page"](tmp)
    html = open(page, encoding="utf-8").read()
    assert n == 1 and total == 3, (n, total)
    assert html.count('class="delf"') == 3, "删除按钮数不对"
    assert 'action="/p2z-del"' in html, "删除表单必须同源"
    assert "8088" not in html, "不得出现其它端口"
    assert "中英对照" in html and "纯中文" in html and "原文" in html

    # 2) 入口（import 期就会调用 —— 必须测）
    ent = ns["entry_html"](tmp, page)
    assert "/p2z-hist" in ent and "次翻译" in ent, ent[:120]

    # 3) 补丁能编译
    patched = subprocess.run([sys.executable, f"{ROOT}/apply.py", os.path.join(os.path.dirname(ROOT), "pdf2zh_next", "gui.py"),
                              "--out", f"{tmp}/gui_patched.py"], capture_output=True, text=True)
    assert patched.returncode == 0, patched.stderr
    assert "hermes-hist-entry" in open(f"{tmp}/gui_patched.py", encoding="utf-8").read()
    print("自测全部通过 ✓ （页面/入口/补丁编译）")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
