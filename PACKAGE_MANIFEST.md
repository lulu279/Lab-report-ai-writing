# 包清单与事实源（PACKAGE_MANIFEST）

版本：1.2（2026-10-26）  
适用：只保留本文件夹、不保留整个项目历史材料时使用。

> 公开仓库版：不含课程讲义 PDF 与官方空白模板 DOCX（版权/教师信息）；本地完整版请从原目录加入。全文范例为作者本人历史课程作业，仅用于写法学习，勿作为自己的作业提交。

## 1. 一句话

**规范在 `01_Governance/`，工序在 `02_Workflows/`，任务材料由用户提供，历史成品只作范例、不作数据源。**

## 2. 包内有什么

| 位置 | 内容 | 用途 |
|---|---|---|
| `00_START/START_HERE.md` | 冷启动入口 | 新 AI 先读这一页 |
| `00_START/INPUT_PACK.md` | 任务输入清单 | 开工前填；缺项就停 |
| `00_START/COVER_FIELDS.md` | 封面字段 | 课程硬性四项，缺一可能 0 分 |
| `00_START/COURSE_HANDOUT_2026.pdf`（公开仓库未上传） | 课程讲义（2026） | 目的/原理/步骤/思考题/课程规则；含教师姓名/版权，仅个人学习使用，不公开分享 |
| `01_Governance/` | 风格、格式、诚信、来源、人工介入规范 | 规范事实源 |
| `02_Workflows/` | 实验报告、首次起草、改稿、数据图表、论文、综述 | 执行工序 |
| `03_Templates/COURSE_TEMPLATE.docx`（公开仓库未上传） | 官方空白模板 | 版式下限 |
| `03_Templates/ORIGINAL_PROMPT.txt` | 用户原始通用提示词 | 历史要求，已被规范吸收；保留追溯 |
| `03_Templates/` 其余 | 任务、项目、范例卡、反馈、交付说明、提示词 | 可直接复制的表 |
| `04_Examples/*_GOLD/SILVER.md` | 5 张范例卡 | 选 1 个最相关的学写法 |
| `04_Examples/STYLE_EVOLUTION.md` | 6 组初稿→终稿逐段对照 | 学“终稿高明在哪” |
| `04_Examples/full/IR_GOLD_FULL.docx/.md` | IR 全文范例（版式/多图/峰归属） | 整篇结构与图位参考 |
| `04_Examples/full/GPC_SILVER_FULL.docx/.md` | GPC 全文范例（数据链） | 淋洗曲线→标定→分子量参考 |
| `05_Tools/build_report_docx.py` | 报告 DOCX 生成器（纯标准库） | 封面/标题/正文/图/表/页码；`--draft`/`--audit` |
| `05_Tools/docx_text.py` | DOCX 文本/表格提取器 | 读范例、查正文、做污染检查 |
| `05_Tools/check_contamination.sh` | 旧范例数值污染检查 | 交付前扫“是否误用旧数据” |
| `05_Tools/sanitize_docx_meta.py` | DOCX 元数据匿名化 | 收录历史范例前去掉作者姓名 |
| `05_Tools/RUN_PYTHON.md` | 解释器选择说明 | 沙箱 Skulpt 不能跑生成器；用宿主机 CPython |
| `05_Tools/FIGURES.md` | 图的来源与降级方案 | 无绘图库时交数据+plot_spec，不伪造图 |
| `05_Tools/pdf_text.py` | PDF 文本提取 | 读讲义/文献；需宿主机 pypdf |
| `05_Tools/examples/make_sample_fig.py` | 合成 PNG 生成脚本 | 只验证嵌图，不替代 Origin/Excel |
| `05_Tools/examples/` | 合成烟雾测试（MD/PNG/DOCX） | 验证生成器；数值非实验数据 |
| `05_Tools/build_delivery_docx.py` | 生成本系统交付文档 | 只用于 `00_交付文档.md`，不是报告生成器 |
| `VERSION` | 版本号/日期 | 打包与盲测记录引用 |
| `06_Evaluation/` | 评分表、基线审计、盲测计划、runs/ | 验收与回归 |
| `07_Projects/` | 2026 课程项目状态、提交清单 | 历史快照 + 可复用清单 |
| `99_Archive/` | 归档索引 | 只作追溯；包内没有旧文件 |

## 3. 包内没有什么

以下内容**不在包内**，必须由用户作为本次任务输入提供，或只在原项目目录中存在：

- 本次实验的原始数据、仪器导出、处理脚本；
- 8 份历史报告的成品 DOCX/PDF/XLSX；
- Origin 工程、图片源文件、交付说明原件；
- 除 `00_START/COURSE_HANDOUT_2026.pdf` 之外的讲义/教材/文献；
- 历史脚本（`SCRIPT_INDEX.md` 列出的绝大多数脚本）。

不要因为卡片里写了路径，就认为文件存在。见 `04_Examples/README.md` 和 `05_Tools/SCRIPT_INDEX.md` 的“历史/包外”标注。

## 4. 事实源优先级

冲突时按以下顺序：

1. 课程/期刊正式要求与模板（本次最新版）；
2. 用户本次明确要求（以最后一条为准）；
3. `01_Governance/` 已批准规范；
4. `02_Workflows/` 工序；
5. `03_Templates/` 模板；
6. `04_Examples/` 范例（只学写法，不取数值）；
7. `07_Projects/`、`06_Evaluation/BASELINE_AUDIT.md`、`99_Archive/` 历史快照（只追溯，不代表当前状态）。

同一规则在多个文件出现时，以 `01_Governance/` 为准；`00_交付文档.md`、`README.md` 只做导航和摘要，不另立规则。

## 5. 本次任务输入的最小集合

- 讲义对应章节（目的/原理/步骤/思考题）；
- 原始数据 + 列含义/单位/样品/条件；
- 课程模板或明确版式要求；
- 封面四项；
- 交付格式与截止。

缺任何一项，先停下来问。见 `00_START/INPUT_PACK.md`。

## 6. 版本与校验

- 版本：1.2
- 日期：2026-10-26
- 文件数：以仓库实际文件为准（公开版不含 2 份课程材料；生成 `SHA256SUMS.txt` 后 +1）
- 哈希清单：`SHA256SUMS.txt`（打包前生成；不要手写）
- 打包前清理：删除 `__pycache__/`、`*.pyc`、临时文件；它们不应进入 zip。
- 修改记录：`CHANGELOG.md`

## 7. 给新 AI 的三句话

1. 先填 `INPUT_PACK` 和 `COVER_FIELDS`，再读写作规范。
2. 数值只来自本次 DATA；范例里的数一个都不能搬。
3. 写完先过 `07_Projects/高分子物理实验2026/SUBMISSION_CHECKLIST.md`，没验证就写“未验证”。
