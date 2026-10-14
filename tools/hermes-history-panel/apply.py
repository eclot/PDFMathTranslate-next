#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 Hermes 历史页补丁打到目标 gui.py 上（幂等；锚点失效立即报错）

用法:
    python3 apply.py <目标 gui.py> [--out 输出.py]
"""
import argparse, ast, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = open(os.path.join(HERE, "gen.py"), encoding="utf-8").read().split('if __name__ == "__main__":')[0].rstrip() + "\n"

INSTALL = open(os.path.join(HERE, "install_block.py"), encoding="utf-8").read()
ENTRY = ("    gr.HTML(_HERMES_HIST_HTML)  # hermes-hist-entry\n"
         "    _hermes_orig_launch = demo.launch\n"
         "    def _hermes_launch(*a, **kw):\n"
         "        _hermes_install_del_route()\n"
         "        return _hermes_orig_launch(*a, **kw)  # 原样调用；启动方式不变\n"
         "    demo.launch = _hermes_launch\n")
BLOCK = ("\n# ───────── Hermes 补丁（安全版）：独立历史页（7860 内删除）+ 页面入口 ─────────\n"
         + GEN + INSTALL +
         "\n_HERMES_ROOT = __import__(\"os\").path.realpath(\"pdf2zh_files\")\n"
         "_HERMES_HIST_PAGE, _H, _T = write_history_page(_HERMES_ROOT)\n"
         "_HERMES_HIST_HTML = entry_html(_HERMES_ROOT, _HERMES_HIST_PAGE)\n"
         "# ───────── 补丁结束 ─────────\n")

ANCHORS = [
    "if not config_fake_pdf_path.exists():",   # 2.9.0 的插入点 1
    ") as demo:\n",                            # 2.9.0 的插入点 2
]


def apply(text):
    for a in ANCHORS:
        if a not in text:
            raise SystemExit("锚点失效，需人工适配: %r（上游可能改了 gui.py 结构）" % a[:40])
    i = text.index(ANCHORS[0])
    out = text[:i] + BLOCK + "\n" + text[i:]
    j = out.index(ANCHORS[1]) + len(ANCHORS[1])
    out = out[:j] + ENTRY + out[j:]
    ast.parse(out)                     # 必须能编译
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--out")
    a = ap.parse_args()
    src = open(a.target, encoding="utf-8").read()
    if "hermes-hist-entry" in src:
        print("已打过补丁，跳过")
        return
    out = apply(src)
    dst = a.out or a.target
    open(dst, "w", encoding="utf-8").write(out)
    print("补丁完成:", dst, len(out), "字节 (+%d)" % (len(out) - len(src)))


if __name__ == "__main__":
    main()
