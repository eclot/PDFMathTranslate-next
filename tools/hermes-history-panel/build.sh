#!/bin/sh
# 从本仓库自带的 pdf2zh_next/gui.py（= 上游原版）现打补丁，产出 dist/gui.py
set -e
cd "$(dirname "$0")"
python3 apply.py ../../pdf2zh_next/gui.py --out dist/gui.py
python3 tests/selftest.py
echo "产物: tools/hermes-history-panel/dist/gui.py"
