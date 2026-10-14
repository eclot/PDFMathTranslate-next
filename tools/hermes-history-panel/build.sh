#!/bin/sh
# 从本仓库自带的 pdf2zh_next/gui.py（= 上游原版）现打补丁，产出 artifact/gui.py
set -e
cd "$(dirname "$0")"
python3 apply.py ../../pdf2zh_next/gui.py --out artifact/gui.py
python3 tests/selftest.py
echo "产物: tools/hermes-history-panel/artifact/gui.py"
