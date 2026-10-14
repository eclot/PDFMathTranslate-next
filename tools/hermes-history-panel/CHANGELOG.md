# 变更记录

## v6 — 历史页"打开即最新"
新增同源 `GET /p2z-hist`：每次访问重新扫描并生成后返回（新翻译后无需回主页刷新）。入口链接与删除结果页均指向它。

## v5 — 删除功能改到 7860
`POST /p2z-del` 通过"包一层 launch（原样调用）+ 守护线程把路由插到最前"实现，同源表单提交。
- ✗ 迭代中曾把删除接口放到 8088 → 被用户否决（要求一切都在 7860），已改为同源并撤销 8088 改动。
- ✗ `entry_html()` 解包 bug（`_, n, total = _collect()`）导致容器 crash-loop → 自测必须覆盖 import 期执行的**每个**函数。

## v4 — 每个文件加删除按钮
（该版实现放在 8088，已被 v5 取代。）

## v3 — 独立历史页
从主页内嵌折叠列表改为**独立页面**：页面为静态 HTML，经 Gradio 已有路由 `/gradio_api/file=<abs>.html` 提供（`content-disposition: inline`），按每次翻译分组、列出全部产物。

## v2 — 安全版入口（纯 UI）
只在 `with gr.Blocks(...) as demo:` 内插一个 `gr.HTML` 区块。
- ✗ v1 曾接管 `demo.launch`、自建 FastAPI + `gr.mount_gradio_app` + 自跑 uvicorn → 前端永久"加载中" → 回滚。

## v1 — 参数优化（非本补丁范围）
qps 4→8、term_qps 4→8、pool_max_workers→16、关自动术语提取、关 thinking。
