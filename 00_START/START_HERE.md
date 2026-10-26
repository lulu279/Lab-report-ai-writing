# START HERE：新 AI 的冷启动入口

> 公开仓库版：`00_START/COURSE_HANDOUT_2026.pdf` 与 `03_Templates/COURSE_TEMPLATE.docx` 未上传；请从本地完整包加入后再按本页执行。

> 如果你只拿到这个文件夹和一份新任务，先读完本页，再按顺序读文件。不要从历史报告里找本次数据。

## 0. 这个系统是什么

一套《高分子物理实验》课程报告的**写作、改稿、数据处理、图表、DOCX 交付与验收**规范。

它**不包含**本次实验的原始数据、仪器导出、课程讲义之外的参考报告、Origin 工程；这些必须由用户作为“本次任务输入”提供。见 `PACKAGE_MANIFEST.md`。

## 1. 必读顺序

1. `00_START/START_HERE.md`（本页）
2. `00_START/INPUT_PACK.md`：先填任务输入；缺关键项就停下来问。
3. `01_Governance/SCIENTIFIC_INTEGRITY.md`、`SOURCE_POLICY.md`、`HUMAN_IN_THE_LOOP.md`
4. `01_Governance/STYLE_PROFILE.md`、`FORMAT_PROFILE.md`
5. `02_Workflows/EXPERIMENT_REPORT.md` → `FIRST_DRAFT.md` → `REVISION_WORKFLOW.md`
6. `04_Examples/README.md`：只选 1 个最相关的范例（优先 `full/` 里的全文）
7. `03_Templates/COURSE_TEMPLATE.docx`、`DELIVERY_NOTE.md`
8. `05_Tools/FIGURES.md`：图从哪来；无绘图能力时交数据+绘图说明，不伪造图
9. `05_Tools/RUN_PYTHON.md` → `05_Tools/build_report_docx.py`：确认 Python 解释器并生成报告 DOCX
10. `07_Projects/高分子物理实验2026/SUBMISSION_CHECKLIST.md`：交付前逐项签核

## 2. 标准执行顺序

```text
填 INPUT_PACK → 核对数据列/单位/样品 → 建证据矩阵 → 选 1 个范例
→ 写 FIRST_DRAFT（一节一个论点）→ 四遍改稿（论证/证据/段落/压缩）
→ 生成图 + 表 → build_report_docx.py 生成 DOCX → 逐项审计
→ 补交付说明 → 学生确认/改写/署名 → 提交
```

## 3. 硬性停止条件

出现以下任一情况，先停下来问用户，不得猜、不得编：

- 封面四项（班级/姓名/学号/实验内容）缺失或不完整；
- 没有本次讲义/思考题，或不知道实验要求；
- 原始数据的列含义、单位、样品身份不明确；
- 没有课程模板或明确的版式要求；
- 需要声称“已渲染/已运行/已验证”，但实际没做；
- 课程禁止完全 AI 写作，而用户要求直接提交整篇 AI 生成稿。

## 3.1 运行前自检

```bash
python3 -c "import zipfile; print('OK')"
```

如果报 `NotImplementedError`/`Skulpt`，不要继续跑生成器；按 `05_Tools/RUN_PYTHON.md` 换宿主机 CPython 或 qoder_bridge。没有可用 CPython 时，交 Markdown + 图 + 表，并写“DOCX/PDF 未生成”，不要手工伪造。

讲义 PDF 打不开时，用 `python3 05_Tools/pdf_text.py 00_START/COURSE_HANDOUT_2026.pdf --pages 1-10` 抽文本；`pypdf` 在宿主机可用。

## 4. 三条底线

1. **数据只来自本次 DATA 文件**；范例、旧报告、卡片里的数值一律不能当本次结果。
2. **结论不得超出证据**；推测写“可能/提示/尚不能确定”，不能写成事实。
3. **不伪造验证**；没打开、没渲染、没运行，就写“未验证”。

## 5. 包内/包外

- 包内：规范、工作流、模板、范例卡、2 份全文范例、课程讲义、空白模板、工具脚本。
- `COURSE_HANDOUT_2026.pdf` 含教师姓名/版权，仅个人学习使用；公开分享前删除或脱敏。
- 包外：本次原始数据、旧报告成品、旧脚本、Origin 工程、图片源文件。
- 历史快照：`06_Evaluation/BASELINE_AUDIT.md`、`07_Projects/`、`99_Archive/` 只用于追溯，不代表当前文件仍然存在。

详见 `PACKAGE_MANIFEST.md`。

## 6. 如果你只做一件事

先填 `00_START/INPUT_PACK.md` 和 `00_START/COVER_FIELDS.md`。这两张表填不完整，后面的写作和排版都会返工。
