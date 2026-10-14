# pdf2zh-next 历史页补丁（Hermes）

在 **PDFMathTranslate-next (pdf2zh-next) 的 Gradio 界面**里加两件事，**全部跑在 7860 端口**：

1. **独立历史页** `/p2z-hist`（每次打开即时重扫生成）：按"每次翻译"一张卡片，列出该次的全部产物（原文 / 中英对照 dual / 纯中文 mono）+ 时间 + 大小，点文件名直接下载。
2. **每个文件一个删除按钮**（同源 `POST /p2z-del`）：确认后删除并立即重生成页面。

## 这个分支是什么
本分支只**新增** `tools/hermes-history-panel/`，**不改动上游任何文件** —— 因此 `git merge upstream/main` 永不冲突。
`artifact/gui.py` 是可直接使用的成品（打好补丁的 gui.py），`build.sh` 可从上游原版重新生成。

分支：`hermes/history-panel`；上游：`PDFMathTranslate-next/PDFMathTranslate-next`；兼容基线：**v2.9.0**。

## 部署方式（为什么是"挂文件"而不是自建镜像）
容器镜像不动，只把补丁后的 gui.py 挂进容器覆盖同名文件：
```
-v /home/ethan/pdf2zh/patch/gui.py:/usr/local/lib/python3.13/site-packages/pdf2zh_next/gui.py
```
好处：升级/回滚只需换这一个挂载。代价：镜像升级后要重打补丁（见下）。

## 升级上游版本时
```sh
git fetch upstream && git merge upstream/main          # 本分支不改上游文件 → 不冲突
./tools/hermes-history-panel/build.sh                  # 重打补丁（锚点失效会直接报错）
python3 tools/hermes-history-panel/deploy/deploy.py    # 推送 + 重建 + 验收
```

## 硬规则（踩过的坑）
- **一切都在 7860**，不引入任何其它端口。
- **绝不接管/替换 `demo.launch` 本体**：只允许"包一层 + 原样调用"，否则页面永久卡在加载中。
- 新增路由必须 `routes.insert(0, ...)` 插到**最前**（Gradio 的 `/` 兜底在后），并在 `demo.app` 就绪后由守护线程安装。
- 部署前必须 `ast.parse` + 跑 `tests/selftest.py`（曾漏测 `entry_html` → 容器 crash-loop）。
- 删除需要执行者对目录有写权限：`setfacl -R -m u:agent:rwX <目录>`（含 `-d` 默认 ACL）。
- 按钮不要用 emoji（无字体环境显示空框）。
- **必须用真实浏览器（Chrome CDP）验收**，HTTP 200 ≠ 页面可用。
- 判断"有没有新版"看 **digest / 镜像内实测版本**，不要看 tag 名或 `last_updated`。

## 许可证
上游为 AGPL-3.0；本目录是对其 `gui.py` 的补丁与配套脚本，保留原版权与许可证（见仓库根 LICENSE）。
