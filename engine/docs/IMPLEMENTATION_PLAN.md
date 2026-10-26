# 科研 AI 工作引擎 v0.1：DSC 原型完整实施方案

## 0. 产品目标与定位

将用户现有的 DeepSeek 规则库转化为可执行的本地 DSC 研究辅助工作流。第一版仅验证从规范化数据到可编辑草稿、图表及日志的端到端闭环，不承诺一轮完成可直接提交的真实实验报告。

### 产品验收口径

- 数据解析、积分与图表完全由本次输入驱动；不读取历史报告的具体峰温和热焓。
- 所有重要数值可追溯到输入数据的 SHA-256 哈希、配置、算法和计算版本。
- 计算失败时阻断后续“完成”状态。
- 交付的 Word 不等于已审核科学结论；AI 讨论只提供待审核草稿。
- 基础组件能够脱离外部 API 在本地运行。

## 1. 数据流与职责边界

```text
输入 CSV + 配置 JSON/YAML
   │
   ├─► 配置验证（schema.py）──失败→停止
   └─► CSV 解析（loader.py）───失败→停止
                      │
                 事件积分（calculations.py）
                      │
               数值质量门槛（validation.json）
                      ├── FAIL ──► 留存 results/validation/run_log，不输出 DOCX
                      └── PASS/WARN
                              │
                     绘图（figures.py）
                              │
                     可选 AI 讨论（ai.py）
                              │
                     Word 草稿（report.py）
                              │
                     人工科学/视觉审核（尚未自动化）
                              │
                     ZIP 交付与反馈
```

**明确区分：** 规则数据库负责写作风格，程序计算层负责数值，AI 只负责备选的叙述草稿；结论是否科学成立由使用者审核。

## 2. 模块接口（首版已实现）

| 模块 | 接口 | 输入 | 输出 / 失败 |
|---|---|---|---|
| `schema.py` | `parse_config(raw: dict) -> Config` | JSON/YAML 映射 | 校验过的 Config；失败抛 `InputError` |
| `loader.py` | `parse_csv(path, config) -> DataFrame` | CSV、Config | 五列规范化 DataFrame；失败抛 `InputError` |
| `calculations.py` | `analyze(df, config) -> (events, issues, bundle)` | DataFrame、Config | 事件、错误与警告、校正曲线数据 |
| `figures.py` | `create_figures(df,curves,config,folder) -> list[str]` | 数据、基线 | SVG/PNG 路径列表 |
| `ai.py` | `generate_discussion(results,config,knowledge,model) -> str` | 已计算结果、风格摘要 | 未审核讨论；API 失败显式标记 |
| `report.py` | `build_docx(out,results,config,figures_dir,discussion=None)` | 结果、图像、可选文字 | DOCX 草稿 |
| `pipeline.py` | `run(data_path,config_path,run_root,use_ai=False,model=None) -> Path` | 两个文件路径 | 唯一运行目录；数值 FAIL 无 DOCX |
| `pipeline.py` | `pack_outputs(run_dir) -> Path` | 运行目录 | 包含可追溯材料的 ZIP |
| `cli.py` | `python -m research_engine.cli ...` | CLI 参数 | `RUN_DIR` 与 `OUTPUT_BUNDLE` |
| `app.py` | `streamlit run app.py` | 上传表单 | 下载 ZIP / DOCX、显示质量标记 |

### 推荐后续插件接口（未实现）

```python
class ExperimentAnalyzer:
    kind: str
    def validate(self, raw, metadata) -> list[dict]: ...
    def analyze(self, raw, config) -> dict: ...
    def figures(self, raw, results, outdir) -> list[str]: ...

class DocumentRenderer:
    def create(self, validated_results, style, output_path) -> str: ...

class QualityGate:
    def check(self, data, results, files) -> dict: ...
```

等 DSC 真实数据回归验证后，再为 TGA、FTIR 等实现同一契约，不建议马上开发全套实验插件。

## 3. 输入格式契约

### 3.1 CSV（UTF-8, 逗号分隔）

| 列名 | 单位 | 描述 | 必需 |
|---|---|---|---|
| `sample_id` | 无 | 必须匹配配置文件 sample_id | 是 |
| `segment` | 无 | 明确 H1/C1/H2/C2 等阶段；不自动分段 | 是 |
| `time_s` | s | 每个样品/扫描段严格递增的真实采样时间 | 是 |
| `temperature_c` | °C | 实际样品温度，不能误用程序设定温度 | 是 |
| `heat_flow_mw` | mW | 经校验的热流记录；不可直接填 W/g | 是 |

原始仪器文件单位必须先确认，不能单凭列名推断。每个样品每个阶段至少 15 点，每个积分窗口至少 21 点；这是初版技术防错门槛，不能代表测量质量合格。

### 3.2 JSON 示例字段

```json
{
  "dataset_type":"experimental",
  "dataset_label":"2026 DSC run 01",
  "measurement_units":{"time_s":"s","temperature_c":"degC","heat_flow_mw":"mW"},
  "baseline_fraction":0.10,
  "samples":[{
    "sample_id":"PE_01",
    "polymer":"PE",
    "mass_mg":5.0,
    "endotherm_up":true,
    "delta_h0_j_g":null,
    "delta_h0_reference":null,
    "reference_verified":false,
    "cold_crystallization_excluded":null
  }],
  "windows":[{
    "event_id":"PE_01_H1_melting",
    "sample_id":"PE_01",
    "segment":"H1",
    "phase":"melting",
    "start_c":90.0,
    "end_c":120.0
  }]
}
```

上述数字只是说明配置格式，**不是从用户 DSC 报告提取的实际参数**。需要按本次原始曲线人工设置。

- `phase` 可选 `melting`、`crystallization`、`cold_crystallization`；冷结晶被建模为升温过程放热。
- `endotherm_up` 必须由仪器热流符号说明或校验结果确认。
- `delta_h0_j_g` 可留空；留空时绝不凭历史报告自动补全结晶度。
- `cold_crystallization_excluded` 为 `true` 才允许在未提供冷结晶积分的情况下计算结晶度，否则留空并报提示。
- `reference_verified=true` 必须由用户独立确认来源；程序不能自行判断文献可靠性。
- `dataset_type=experimental` 只是操作者声明，程序不能鉴定真实性。

## 4. 计算与质量模型

按时间积分：

\[
\Delta H\,[\mathrm{J/g}]=\frac{\int_{t_a}^{t_b}(\Phi(t)-\Phi_\mathrm{base}(t))dt\,[\mathrm{mJ}]}{m\,[\mathrm{mg}]}
\]

计算中的吸热方向统一成正号；熔融通常为正、结晶通常为负。采用基线锚点窗口平均值构建随时间变化的直线，不直接把热流—温度曲线几何面积当成热量。依赖用户明确的窗口和仪器符号约定。

仅在条件充分时计算：

\[
X_c=\frac{\Delta H_m-|\Delta H_{cc}|}{\Delta H_m^0}\times 100\%
\]

同一升温段有经计算的冷结晶峰时进行修正；若操作者明确排除冷结晶，则以零处理；否则结晶度置 `null` 并标记 `cold_crystallization_not_assessed`。这不是自动的 Tg、复杂多峰拟合或热分析全模型。

### 质量门槛（示范阈值，需真实实验校准）

| 类别 | 触发条件 | 动作 |
|---|---|---|
| 输入 | 必需列缺失、单位不一致、质量非正、时间不递增 | 拒绝运行 |
| 方向 | 峰符号与熔融/结晶类型不匹配 | `FAIL`，阻断 DOCX |
| 基线 | 三种端点比例 5/10/15% 积分焓相对差异 >25% | `FAIL`，阻断 DOCX |
| 基线 | 15%–25% | `WARN`，允许草稿但必须重新审核积分窗口 |
| 结晶度 | 超出 0–100% | `FAIL`，阻断 DOCX |
| 参考文献 | ΔH0 未核验 | `WARN`，不能称为已验证结晶度 |
| 科学判断 | 自动分析模块无法核验机理 | 始终 `NOT_REVIEWED`，人工审核 |
| 版式 | 当前可检查 DOCX 生成成功，但无法在所有系统验证显示 | 始终待目标系统复核 |

**注意：** 基线敏感度不是测量不确定度，也不是通行的仪器方法标准。今后应通过真实 DSC 数据和已知对照结果校准阈值。

## 5. 输出目录契约

```text
runs/<YYYYMMDD_HHMMSS_random>/
├── inputs/
│   ├── data.csv               # 本次标准化输入副本
│   └── config.json            # 显式分析配置
├── manifest.json              # SHA256、版本、单位、是否AI、模型标识
├── results.json               # 所有事件参数及追溯数据
├── validation.json            # 数值及科学审查状态、警告和限制
├── run_log.json               # 草稿状态或阻断原因
├── figures/
│   ├── PE_demo_overview.svg / png
│   ├── PET_demo_overview.svg / png
│   └── <event_id>.svg / png
├── ai_discussion_draft.txt     # 仅启用并成功调用 API 时存在
├── report_draft.docx          # 仅数值通过时生成
└── download_bundle.zip        # 本次全部运行产物
```

`results.json` 的主要字段：

```json
{
  "schema_version":"0.1",
  "run_id":"unique-id",
  "dataset_type":"synthetic",
  "data_sha256":"...",
  "events":[{
    "event_id":"...",
    "sample_id":"...",
    "segment":"H1",
    "phase":"melting",
    "window_c":[90,120],
    "peak_temperature_c":null,
    "integrated_area_mj_endotherm_up":null,
    "enthalpy_j_g":null,
    "crystallinity_pct":null,
    "crystallinity_status":"pending_qualification",
    "baseline_sensitivity_pct":null,
    "method":"linear endpoint mean baseline; trapezoidal time integration"
  }],
  "validation":{"numerical_status":"WARN", "scientific_interpretation_status":"NOT_REVIEWED"}
}
```

`null` 只是字段结构示例，真实运行文件由计算模块填充，不使用此示例值。

## 6. 技术选型与部署

| 层 | 技术 | 理由 |
|---|---|---|
| UI | Streamlit | 上传、结果预览、运行及下载流程开发快速 |
| 解析 | pandas + 配置校验 | 直观核对数据列、样品、缺失点 |
| 计算 | NumPy | 可测试、可复现的积分与峰值计算 |
| 绘图 | Matplotlib | SVG/PNG 可导出，计算数据可追溯 |
| Word | python-docx | 页面、字体、表格、图片可编辑 |
| 配置 | JSON/YAML | 便于保存窗口参数与运行条件 |
| AI | 可选 OpenAI API | 只参与讨论草稿；模型 ID 和 API key 外部提供 |
| 测试 | pytest | 数值边界、异常输入、端到端集成 |

目标环境 Windows + Python 3.11/3.12。Origin 2021 接口以后再独立开发，不把运行失败的 Origin 项目误作为交付文件。

## 7. 在用户电脑上的完整实施步骤

1. 建立 Git 仓库，导入本 ZIP 的源码；把历史 DeepSeek 知识库另存为版本化只读目录。
2. 用 PowerShell 建立 `.venv` 并安装 `requirements.txt`。
3. `python -m pytest -q`，检查测试全部通过。
4. 命令行运行合成数据；查验 `validation.json`、图表和 DOCX 的 SYNTHETIC 标记。
5. `python -m streamlit run app.py` 启动本地界面，上传演示 CSV/JSON。
6. 补充真实原始 DSC 仪器文件、原始脚本或可信导出字段说明；先人工转换为标准五列 CSV。
7. 用实际元数据建立新的分析配置，明确阶段、热流符号、积分窗口、样品质量和 ΔH0 状态。
8. 与真实已知处理值做逐项对照，必要时增加基线方法选项，不能用旧结论替换新积分。
9. 建立输入与原参考报告分离的盲测集，再验证一次完整输出。
10. 只有在质量门槛和人工审查都通过后，才考虑默认生成带正文讨论的报告。

## 8. 真实数据迁移设计（下一版）

- `RawAdapter`：通过独立子模块识别特定仪器版本的 TXT、XLSX；识别不出必须报错、不得猜列。
- `SegmentAnnotator`：从确切程序记录或人工选择中生成 H1/C1/H2/C2；保存边界来源。
- `PeakReviewUI`：在图上交互选取基线窗口与积分范围，保留用户修改记录。
- `ReferenceRegistry`：验证 ΔH0 来源及材料适用范围，保存 DOI 和引用状态。
- `UncertaintyModule`：质量、仪器灵敏度、积分窗口和重复性误差分开处理，不把任一变量误当总误差。
- `TgModule`：只在玻璃化台阶足够明确且中线法定义经确认时给 Tg。
- `ReportComposer`：从课程正式模板或目标期刊模板生成 Word，不复制历史报告数值。
- `VisualQAGate`：本地 Word/LibreOffice 自动渲染与图表错位检查。

## 9. 验收和反馈闭环

上线前验证三种任务：

- **数学单元测试**：纯合成高斯峰，使用解析积分作独立参考；单位、符号和错误输入必须可复核。
- **历史复现测试**：真实 DSC 原始数据 + 元数据输入，与历史结果对照，但历史结果在运行期间完全隔离。
- **新任务留出测试**：用户从未用于知识库构建的实际 DSC 数据；评价输出相对无知识库基线的增益。

每次试运行记录：输入哈希、规则版本、代码版本、每个窗口的积分结果、质量报告、人工修订内容。先验证数值与格式稳定，再尝试减少人工修改轮次。

## 10. 仍需用户补充

最优先：真实 DSC 原始数据、扫描条件/列含义/仪器热流方向、样品质量、原始绘图/积分脚本、实际 Word 模板。没有这些，当前只能证明软件框架通过合成测试，不能证明已重现用户的 DSC 实验。
