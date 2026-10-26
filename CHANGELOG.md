# 变更记录（CHANGELOG）

## 1.3 — 2026-10-26

### 新增/强化

- **标准三线表硬性规则**：所有数据表（条件表、结果表、峰归属表、汇总表）一律使用标准三线表——顶/底 1.5 pt、表头线 0.75 pt、无竖线/左右边框/其他内横线；表头加粗、单位在表头；禁止 Excel 默认网格、全框表、竖线表、斑马纹。
- 规则已写入：`README`、`00_START/START_HERE`、`01_Governance/FORMAT_PROFILE`、`01_Governance/STYLE_PROFILE`、`02_Workflows/FIRST_DRAFT`、`02_Workflows/REVISION_WORKFLOW`、`02_Workflows/EXPERIMENT_REPORT`、`02_Workflows/DATA_FIGURE_DELIVERY`、`03_Templates/ONE_TURN_PROMPTS`、`06_Evaluation/SCORECARD`、`07_Projects/.../SUBMISSION_CHECKLIST`、`PACKAGE_MANIFEST`。
- `build_report_docx.py --audit` 新增三线表边框检查：每张表必须是 top/bottom 1.5 pt、header 0.75 pt、left/right/insideH/insideV none；否则 FAIL。
- `KNOWN_ISSUES` 新增 A8“表格不是标准三线表”。
- 版本号、README、交付文档、包清单同步到 1.3；`00_交付文档.docx` 重新生成。

### 已验证

- 示例 DOCX 的 1 张表通过三线表审计；`--audit` 输出 `three_line_tables=1/1`。
- 生成器仍通过封面/占位符/媒体/表格/主题字体检查。

### 未验证/边界

- 未在 Word/WPS 中逐页渲染；表格的视觉线宽需在 Word/WPS 目检。
- 未修改原稿与 v1.2；本版是独立副本。

## 1.2 — 2026-10-26

### 新增（冷启动与交付）

- `00_START/START_HERE.md`：新 AI 入口、必读顺序、硬性停止条件。
- `00_START/INPUT_PACK.md`：任务输入清单；缺讲义/数据/模板/封面就停。
- `00_START/COVER_FIELDS.md`：封面四项字段表；生成器缺项会报错。
- `00_START/COURSE_HANDOUT_2026.pdf`：课程讲义（原项目根目录副本）。
- `PACKAGE_MANIFEST.md`：包内/包外/历史快照/事实源。
- `02_Workflows/FIRST_DRAFT.md`：从零起草 SOP（目的/原理/步骤/结果/讨论/思考题/结论）。
- `01_Governance/HUMAN_IN_THE_LOOP.md`：AI 辅助 vs 代写、贡献记录、提交闸门。
- `03_Templates/COURSE_TEMPLATE.docx`：官方空白模板副本。
- `03_Templates/ORIGINAL_PROMPT.txt`：原 `提示词.txt` 副本（历史要求，已被规范吸收）。
- `04_Examples/full/IR_GOLD_FULL.docx/.md`、`GPC_SILVER_FULL.docx/.md`：2 份全文范例（去标识化；含旧数据，只学写法）。
- `05_Tools/build_report_docx.py`：纯标准库报告 DOCX 生成器（封面/标题/图/表/页码；`--draft`/`--audit`）。
- `05_Tools/docx_text.py`：纯标准库 DOCX 文本/表格提取器。
- `05_Tools/check_contamination.sh` + `contamination_list.txt`：旧范例高特征数值污染检查。
- `05_Tools/sanitize_docx_meta.py`：匿名化 DOCX 的 creator/lastModifiedBy/description；已用于 2 份全文范例与空白模板。
- `05_Tools/RUN_PYTHON.md`：解释器选择说明（沙箱 Skulpt vs 宿主机 CPython / qoder_bridge）。
- `05_Tools/FIGURES.md`：图从哪来、无绘图库时的降级（数据+plot_spec）、`FIG_PLACEHOLDER` 规则。
- `05_Tools/pdf_text.py`：用 pypdf 抽讲义/PDF 文本；解决“PDF 打不开”时无法读讲义的问题。
- `05_Tools/examples/make_sample_fig.py`：纯标准库重新生成合成 PNG；只验证嵌图，不冒充科学绘图。
- `build_report_docx.py --audit` 改为严格模式：残留 `【待填】/【待核】/【缺图】/TODO/待补` 直接 FAIL；`--draft` 生成时用宽容模式。
- 污染检查列表移除 `998/6.3/5.1/2.29` 等短数字，减少“1998/15.1”子串误报。
- `DELIVERY_NOTE` 文件清单的“验证”列改为 `☐ 待验`，不再预填“已打开/已逐页检查”。
- `build_report_docx.py --margins default|template`：默认 DSC/IR 边距，或官方模板 2.54 cm 边距；不注入模板封面图。
- `05_Tools/examples/`：合成烟雾测试（MD/PNG/DOCX）；数值非实验数据。
- `06_Evaluation/runs/README.md`：盲测记录目录。

### 修正（一致性/合规）

- 新报告统一为：`EXPERIMENT_REPORT` 第 1–10 步 → `FIRST_DRAFT` → **四遍**改稿；废止“新报告只做 1–3 遍”。
- 删样品规则统一为“先问用户，课程/用户要求优先”，不再写“答不上来就删”。
- PL/NMR 等级拆成“内容等级（审计）”与“范例可用级”，解决 Gold/Silver/Reference 冲突。
- `FORMAT_PROFILE` 恢复“官方模板 2.54 cm 优先”的说明；版本 1.1。
- `FORMAT_PROFILE` 增加报告生成器实现、结构审计与 PDF 未渲染声明。
- `DELIVERY_NOTE` 不再预写“AI 使用符合课程规定”，改为学生确认项；增加贡献记录、污染检查、结构审计。
- `SCORECARD`/`SUBMISSION_CHECKLIST` 增加污染检查、学生贡献、PDF 未渲染、结构审计。
- `PROJECT_STATE` 去掉姓名/学号外部指针，标注历史快照。
- `BASELINE_AUDIT`、`ARCHIVE_INDEX`、`SCRIPT_INDEX` 加“历史/包外”标注。
- `SOURCE_POLICY` 的 `提示词.txt` 引用改为包内 `03_Templates/ORIGINAL_PROMPT.txt`；增加 DOCX/PDF 元数据去标识化要求。
- 2 份全文范例与空白模板的 core.xml 作者字段已匿名化；课程讲义 PDF 元数据已匿名化，但正文仍含教师姓名，仅个人使用。
- `TOOLCHAIN`/`KNOWN_ISSUES` 更新实测环境：宿主机 Python 3.14、openpyxl/pypdf 可用；python-docx/numpy/matplotlib 不可用；无 LibreOffice/pandoc；沙箱 `python3` 是 Skulpt shim。
- `README`、`00_交付文档`、`STYLE_PROFILE`、`REVISION_WORKFLOW`、`EXPERIMENT_REPORT`、`ONE_TURN_PROMPTS` 同步新流程与包边界。
- 修正 `SUBMISSION_CHECKLIST` 的错误路径（统一指向 `07_Projects/高分子物理实验2026/`）。
- 修正“删样品”在压缩遍与改稿计划中的残留矛盾；压缩遍也要求先问用户。
- 明确生成器不注入 `COURSE_TEMPLATE.docx` 封面图/占位符；只实现默认版式，`--margins template` 仅切边距。

### 已验证

- `build_report_docx.py` 生成 `05_Tools/examples/sample_report.docx`：1 图、1 表、封面、公式、列表、参考文献、页码；`--audit` 通过（zip/XML/媒体/表格/themeFont=0）。
- 严格模式在缺封面字段时退出 1；`--draft` 可生成草稿并警告；`--audit` 对 `【待填】/【待核】/【缺图】` 退出 1。
- `--margins template` 生成 1440/1440/1440/1440 twips；默认 1247/1219/1134/1332。
- `check_contamination.sh` 在含旧值的合成稿上命中，在干净样例上通过；已移除 `998/6.3/5.1/2.29` 等短数字噪声。
- `docx_text.py` 成功提取 IR/GPC 全文范例为 Markdown。
- `pdf_text.py` 成功抽取课程讲义 29 页文本（pypdf）。
- `sanitize_docx_meta.py` 已匿名化 2 份全文范例与空白模板的 core.xml；讲义 PDF 元数据也已匿名化（正文仍含教师姓名，仅个人使用）。
- `mammoth` 解析样例 DOCX：表格/图片存在；仅报“自定义样式名未识别”（mammoth 的映射限制，不是 DOCX 错误）。
- 所有包内 DOCX 通过 `unzip -t`。

### 最后一致性修正

- `00_交付文档.docx` 封面版本从 1.1 改为 1.2，并加“1.2 新增”一行；依据改为“原始材料不在包内”。
- `DELIVERY_NOTE` 去掉嵌套代码围栏，整份模板保持一个代码块；验证列不预填“已验”。
- `00_交付文档` §8.4 从“10 问”改为“12 问”（实际列 12 条）。
- `START_HERE` 调整读序：先 `FIGURES`（图源）再 `RUN_PYTHON`/DOCX。
- `TOOLCHAIN` 的 pypdf 版本写为 `6.21.x`；IR 的 DOCX 图数与 XLSX 原生图数分开说明。
- 打包前删除 `__pycache__/` 与 `*.pyc`，并在 `PACKAGE_MANIFEST` 写明。

### 未验证/边界

- 未在 Word/WPS 中逐页渲染；PDF 需用户导出。
- 未重跑历史 numpy/matplotlib/Origin 脚本。
- 未跑真正的盲测；`runs/` 仅建目录与规则。
- 未修改原 `科研AI工作系统/`；本版是独立副本。

## 1.1 — 2026-10-26

### 重做重点

- 上一版把封面/页数/交付说明差异当作主线，判断错误。本版改为：**对比初稿与终稿，提炼终稿的写作高明之处**。
- 新增 `04_Examples/STYLE_EVOLUTION.md`：6 组初稿→终稿逐段对照（UV、NMR、DSC、IR、PL、GPC），含字数/表数/文献数变化与原文引例。
- 重写 `01_Governance/STYLE_PROFILE.md`：从“通用规范”改为“终稿的 8 个动作 + 段落模板 + 句子规则 + 取舍原则 + 终稿缺陷”。
- 新增 `02_Workflows/REVISION_WORKFLOW.md`：四遍改稿法（论证→证据→段落→压缩）+ 改稿计划模板 + 假改稿清单。
- 新增 `03_Templates/REVISION_PLAN.md`：可直接复制的改稿计划表。
- 重写 `00_交付文档.md` / `.docx`：以风格演化为骨架；交付完整性降为附录。
- 更新 `README.md`：先读风格演化、风格规范、改稿工作流。
- 更新 `07_Projects/.../SUBMISSION_CHECKLIST.md` 的定位：只管提交完整性，不作为写作质量指标。

### 核心结论

- 终稿的高明不是“更长/更全”，而是：先定问题与范围、选对比轴、用关键数值锚定、机理两环、边界诚实、标题写结论、压缩非证据、结论回原理。
- 终稿并非完美：IR 图号错位/过强结论、NMR δ 不一致、DSC/GPC/IR 错字、PL 结论截断；学习时应“终稿的结构 + 初稿的严谨证据”。

### 未变

- 未修改任何现有实验报告。
- 未在当前宿主重跑 numpy/matplotlib/Origin 脚本。
- 交付 DOCX 仍以结构解析校验为准，未在 Word/WPS 逐页渲染。

## 1.0 — 2026-10-25

### 新增

- 建立 `科研AI工作系统/` 目录：01_Governance、02_Workflows、03_Templates、04_Examples、05_Tools、06_Evaluation、07_Projects、99_Archive。
- 规范：
  - `01_Governance/STYLE_PROFILE.md`
  - `01_Governance/FORMAT_PROFILE.md`
  - `01_Governance/SCIENTIFIC_INTEGRITY.md`
  - `01_Governance/SOURCE_POLICY.md`
- 工作流：
  - `02_Workflows/EXPERIMENT_REPORT.md`
  - `02_Workflows/DATA_FIGURE_DELIVERY.md`
  - `02_Workflows/RESEARCH_PAPER.md`
  - `02_Workflows/LITERATURE_REVIEW.md`
- 模板：
  - `03_Templates/EXEMPLAR_CARD.md`
  - `03_Templates/TASK_BRIEF.md`
  - `03_Templates/PROJECT_STATE.md`
  - `03_Templates/FEEDBACK_LOG.md`
  - `03_Templates/DELIVERY_NOTE.md`
  - `03_Templates/ONE_TURN_PROMPTS.md`
- 范例：
  - `04_Examples/README.md`
  - `04_Examples/UV-Vis_GOLD.md`
  - `04_Examples/DSC_GOLD.md`
  - `04_Examples/IR_GOLD.md`
  - `04_Examples/TGA_SILVER.md`
  - `04_Examples/GPC_SILVER.md`
- 工具：
  - `05_Tools/TOOLCHAIN.md`
  - `05_Tools/SCRIPT_INDEX.md`
  - `05_Tools/KNOWN_ISSUES.md`
  - `05_Tools/build_delivery_docx.py`（标准库 OOXML 生成器）
- 评估：
  - `06_Evaluation/SCORECARD.md`
  - `06_Evaluation/BASELINE_AUDIT.md`
  - `06_Evaluation/BLIND_TEST_PLAN.md`
- 项目：
  - `07_Projects/高分子物理实验2026/PROJECT_STATE.md`
  - `07_Projects/高分子物理实验2026/SUBMISSION_CHECKLIST.md`
- 归档：
  - `99_Archive/ARCHIVE_INDEX.md`
- 主交付：
  - `00_交付文档.md`
  - `00_交付文档.docx`

### 证据来源

- 课程：`高分子物理实验-2026-ver1.pdf`（29 页）、`高分子物理实验-实验报告例.docx`。
- 个人要求：`提示词.txt`（与 `DSC/提示词(1).txt` 相同）。
- 8 份成品报告：PL、IR、UV-Vis、TGA、DSC、NMR、GPC、POM。
- 交付说明：`DSC/DSC实验报告交付/交付说明.txt`、`IR光谱/交付说明.txt`、IR Origin 使用说明、NMR 操作指南。
- 数据/脚本：各实验 `processed/`、`scripts/`、`work/`、`_work/`。
- 核验：DOCX/XLSX zip+XML、PDF 页数、PNG 尺寸/DPI、chart part 数量。

### 决策

- 默认格式采用 DSC/IR 成品（宋体+Times、10.5 pt、1.5 倍行距、A4、2.20/2.15/2.00/2.35 cm），不采用 UV 的无衬线/1.15 倍、NMR/GPC 的 9 pt/3.17 cm。
- 内容范例：UV/DSC/IR/PL 为 Gold；TGA/GPC/NMR 为 Silver；POM 为 Reference。
- 封面合规列为 P0：8/8 份均需补班级/姓名/学号。
- 不直接修改用户现有报告；只诊断并给出下一步。
- 不声称当前宿主已重跑 numpy/matplotlib/Origin；工具链文档如实写边界。

### 已知缺口

- 8 份报告均未补封面；4 份无 PDF；TGA 无 XLSX；NMR xlsx 无原生图。
- IR 图号错位/无 PDF/说明数字不一致；TGA 0 表/编号跳号；GPC 图 3 无图注；POM 图 6 引用无图注/文件过大。
- UV 原始 CSV 不在工作区；DSC 交付说明页数/路径不一致；POM 原始照片未单独归档。
- 未做完整科学同行评审；未复算全部原始数据；未在当前宿主重跑历史脚本/Origin。

### 下一步（1.1 计划）

- 补 8 份封面与 4 份 PDF。
- 修复 IR/TGA/GPC/POM/NMR 图/表/编号问题。
- 生成 TGA XLSX；补 NMR 原生图或说明。
- 统一 UV/NMR/GPC 版式。
- 用 TGA、GPC 做首轮盲测，按 `BLIND_TEST_PLAN.md` 记录并更新规范。
