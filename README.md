# 个人科研 AI 工作系统（高分子物理实验版）

版本：1.3（2026-10-26）  

> 公开仓库版：不含课程讲义 PDF 与官方空白模板 DOCX（版权/教师信息）；本地完整版请从原目录加入。全文范例为作者本人历史课程作业，仅用于写法学习，勿作为自己的作业提交。

入口：先读 `00_START/START_HERE.md`，再按任务查文件。  
包清单：`PACKAGE_MANIFEST.md`（包内/包外/历史快照）。

## 这是什么

把 6 组“初稿/早期完整版 → 终稿”对照、课程讲义、官方空白模板、2 份全文范例、交付说明和踩坑记录，整理成一套可复用的**写作、改稿、数据处理、图表、DOCX 交付与验收**系统。核心不是格式检查，而是回答：

1. 终稿相比初稿高明在哪里？
2. 哪些写法可以复用到下一次？
3. 初稿里哪些严谨的东西不能在压缩时丢掉？

一句话：**终稿把“数据报告”改造成了“有论点、有取舍、可评分的课程报告”**。

> 本包**不含**本次实验的原始数据、仪器导出、旧报告成品、Origin 工程；这些是“本次任务输入”，不是系统的一部分。见 `PACKAGE_MANIFEST.md`。

## 先读这五份

1. `00_START/START_HERE.md`：冷启动入口、硬性停止条件。
2. `00_START/INPUT_PACK.md` + `00_START/COVER_FIELDS.md`：开工前填，缺项就停。
3. `04_Examples/STYLE_EVOLUTION.md`：6 组初稿→终稿逐段对照（UV、NMR、DSC、IR、PL、GPC）。
4. `01_Governance/STYLE_PROFILE.md`：8 个动作、段落模板、句子规则、取舍原则。
5. `02_Workflows/FIRST_DRAFT.md` → `02_Workflows/REVISION_WORKFLOW.md`：从零起草 + 四遍改稿。

## 目录

```text
00_START/                  冷启动入口、输入包、封面字段、课程讲义
00_交付文档.md / .docx     总交付文档（风格演化摘要）
01_Governance/             风格、格式、诚信、来源、人工介入规范
02_Workflows/              实验报告、首次起草、改稿、数据图表、论文、综述
03_Templates/              课程空白模板、任务/项目/范例卡/反馈/交付说明/提示词
04_Examples/               5 张范例卡 + 风格演化 + full/ 2 份全文范例
05_Tools/                  报告 DOCX 生成器、DOCX 文本提取、污染检查、工具链
06_Evaluation/             评分、基线审计、盲测计划、runs/
07_Projects/               课程项目状态与提交清单（历史快照）
99_Archive/                旧版/重复件归档索引（包外）
PACKAGE_MANIFEST.md        包内/包外/事实源
VERSION                    版本号
CHANGELOG.md               版本记录
```

## 快速开始

1. **写新报告**：填 `00_START/INPUT_PACK.md` 和 `COVER_FIELDS.md` → `02_Workflows/EXPERIMENT_REPORT.md` 第 1–10 步 → `FIRST_DRAFT.md` 起草 → `REVISION_WORKFLOW.md` 做四遍 → `build_report_docx.py` 生成 DOCX → `07_Projects/高分子物理实验2026/SUBMISSION_CHECKLIST.md` 验收。
2. **改旧报告**：先读 `STYLE_EVOLUTION.md` 找同实验的终稿动作，再按 `REVISION_WORKFLOW.md` 做四遍。
3. **选范例**：`04_Examples/README.md`；优先 `full/` 里的全文，只选 1 个最相关的。
4. **用提示词**：`03_Templates/ONE_TURN_PROMPTS.md` A/B/C/C2。
5. **交付前**：`07_Projects/高分子物理实验2026/SUBMISSION_CHECKLIST.md` + `05_Tools/check_contamination.sh`。

## 三条写作规则 + 一条格式硬性（本版核心）

1. **先问题后数据**：每节先有对比轴，再放数值；不回答任务的样品/结论先问用户能不能删，不要擅自删。
2. **证据链**：每个结论至少一个数（带单位），每个排除点给反事实或原因，每个机理至少两环。
3. **压缩非证据**：删背景/步骤/重复表；保留数值、排除理由、不确定度、边界。
4. **表格三线表**：所有数据表必须用标准三线表（顶/底 1.5 pt、表头线 0.75 pt、无竖线/内横线）；表题在上，单位在表头。不要用全框表、竖线表、斑马纹。

## 当前项目状态（历史快照）

- 6 组初稿→终稿对照已完成；终稿的结构与取舍可复用，但仍有图号/过强结论/错字等问题（见 `STYLE_PROFILE.md` 第 5 节）。
- 8 份历史报告与原始数据**不在本包内**；`06_Evaluation/BASELINE_AUDIT.md` 和 `07_Projects/` 只是 2026-10-26 的快照，文件路径可能已失效。
- 本版没有修改任何现有报告；没有在当前宿主重跑历史 numpy/matplotlib/Origin 脚本。

## 边界

- 本系统是文档、流程与轻量工具，不自动训练模型。
- 不替代实验者的判断、原始记录与署名；课程禁止完全 AI 写作，见 `01_Governance/HUMAN_IN_THE_LOOP.md`。
- `05_Tools/build_report_docx.py` 只用 Python 标准库生成 DOCX；PDF 需在 Word/WPS 中导出，未导出就写“未渲染/未验证”。
- 本包未在 Word/WPS 中逐页渲染；结构校验（zip/XML/媒体/表格）见 `build_report_docx.py --audit`。
