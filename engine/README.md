# Research DSC Engine v0.3

把**标准化 DSC 数据**变成可追溯的分析结果与 Word 草稿，并附带一个**只能查阅、受控执行**的科学公式注册库。所有数值由本地确定性代码计算，AI 最多只能"提议方法"，不能生成或执行公式代码。

本目录是 [`lulu279/Lab-report-ai-writing`](https://github.com/lulu279/Lab-report-ai-writing) 仓库中 `00–07` 写作与治理规则层的**可执行部分**：前者规定"怎么写、怎么验收"，这里负责"怎么算、怎么留痕、怎么出草稿"。

| 项目 | 状态 |
|---|---|
| 版本 / 日期 | v0.3 / 2026-10-26 |
| 代码规模 | 约 1 800 行 Python（引擎 + 测试 + 界面） |
| 离线测试 | 29 项（v0.3 发布记录）；本次复跑 19 项，全部通过（见第 10 节） |
| 真实仪器数据 | **未接入** |
| 真实 AI API 调用 | **未执行** |
| Streamlit 界面 | 代码完成，**未在目标机器实测** |
| 第三方源码 | 未复制、未 vendor |

---

## 1. 它解决什么问题

DSC 报告最容易出的错不是"不会积分"，而是**边界悄悄失守**：单位被猜、基线随手画、把历史报告的峰值当成本次结果、AI 编出一个不存在的公式、数值明显不合理却照样生成了 Word。

这个引擎把一条保守的流水线固定下来：

1. 输入必须显式声明单位、样品质量、吸热方向、扫描分段和积分窗口，缺项直接拒绝；
2. 峰面积、峰温、焓变、结晶度用固定代码计算，每个结果带方法、基线参数和数据哈希；
3. 数值检查为 `FAIL` 时**不生成报告**，只保留证据链与错误记录；
4. 报告草稿永远标注"待人工审核"，合成数据永远带 `SYNTHETIC` 标识；
5. 新增的 13 张公式卡中，只有通过基础数值测试的 9 个允许执行，其余只能查阅。

## 2. 能做什么 / 不能做什么

**已实现**

- 读取显式分段的 UTF-8 CSV（`sample_id, segment, time_s, temperature_c, heat_flow_mw`）与 JSON/YAML 配置；
- 端点线性 / 端点常数两种基线，按测量时间梯形积分，输出峰温、峰面积、质量比焓变；
- 在参考焓已声明且冷结晶已评估的前提下计算结晶度；
- 基线窗口敏感度检查（5% / 10% / 15% 端点比例）；
- 每个样品的全扫描曲线、每个事件的积分示意图（PNG + SVG）；
- `results.json`、`validation.json`、`manifest.json`（输入 SHA-256）、`run_log.json`、可编辑 DOCX 草稿、打包 ZIP；
- 命令行与 Streamlit 双入口；
- 可选的 OpenAI-compatible **方法规划器**：只输出方法 ID、窗口与基线建议，经本地白名单校验和人工确认后才执行；
- 独立的公式注册库：DSC / TGA / UV-Vis / FTIR / GPC / ¹H NMR 共 13 张卡，9 个带数值测试的执行器。

**明确没有实现**

- 不支持任意仪器专有 TXT 导出、自动列名映射、热流单位猜测或自动分段；
- 不计算 Tg、不分解重叠峰、不做仪器标定、不做误差传播；
- 没有量纲引擎，单位只按每个方法的静态契约校验；
- 不把 TGA / FTIR / GPC / NMR 的公式接入 DSC 端到端流水线，它们只是独立计算器；
- 不判断科学结论是否正确，不生成可直接提交的作业；
- 没有真实实验数据案例，因此**不存在科学准确性的实测评估**。

## 3. 架构

```text
标准 CSV ──┐
           ├─► loader / schema ──► calculations ──► validation.json
JSON/YAML ─┘        │                    │              │
                    │                    │              ├─ PASS/WARN ─► figures ─► report.py ─► report_draft.docx
                    │                    │              └─ FAIL ──────► 只写 run_log.json，不出报告
                    │                    └─► results.json（含数据哈希、方法、基线参数）
                    └─► manifest.json（输入文件 SHA-256、AI 计划哈希、运行环境）

可选 AI 规划器：配置 + 每段 ≤32 个均值点 ─► 模型返回 JSON 方案 ─► 本地 schema/白名单校验
                                              ─► 人工勾选确认 ─► 同一 pipeline 执行（计划哈希入档）

公式注册库：method_registry/catalog.json ─► formula_registry.py（9 个执行器）
                                              ─► formula_cli.py / Streamlit 页底
```

三个"闸门"：

1. **输入闸门**（`schema.py` / `loader.py`）：单位必须恰好是 `s / degC / mW`；样品质量、吸热方向必须显式；ID 只允许 `A-Z 0-9 _ -`，防止路径穿越；积分窗口至少 21 个点。
2. **数值闸门**（`calculations.py`）：扫描方向与相态不符、积分符号与吸热方向矛盾、窗口内无可测峰、基线敏感度 >25%、结晶度超出 0–100%，任一触发即 `FAIL` 并阻断报告。
3. **人工闸门**：`scientific_interpretation_status` 与 `document_visual_qa_status` 恒为 `NOT_REVIEWED`；AI 方案必须人工勾选，执行时把方案与配置哈希写入运行记录。

## 4. 目录

```text
engine/
├── app.py                        Streamlit 工作台（报告流水线 + AI 规划 + 公式库）
├── research_engine/
│   ├── schema.py                 配置模型与保守校验
│   ├── loader.py                 CSV 严格解析
│   ├── calculations.py           积分、峰温、结晶度、QC 与敏感度
│   ├── figures.py                PNG / SVG 图
│   ├── report.py                 DOCX 草稿
│   ├── pipeline.py               编排、哈希、阻断、打包
│   ├── cli.py                    报告流水线命令行
│   ├── ai.py                     可选 AI 讨论草稿（不参与计算）
│   ├── planner.py                可选 AI 方法规划 + 本地校验
│   ├── plan_cli.py               规划器命令行（只出方案，不执行）
│   ├── formula_registry.py       公式注册库与 9 个执行器
│   └── formula_cli.py            公式查询 / 计算命令行
├── method_registry/
│   ├── catalog.json              13 张公式卡（机器可读，单一事实源）
│   └── example_*.json            人工编造的测试参数
├── knowledge/                    写作与诚信规则的只读摘录
├── examples/                     合成 DSC 数据与配置（非实验数据）
├── scripts/create_synthetic_fixture.py
├── tests/                        29 项离线测试
├── docs/                         实施计划、资产核对、QA、发布记录
├── 公式注册库_使用与开源方案.md
├── 方法规划器_使用手册.md
└── 开始使用_5步.md
```

## 5. 快速开始

目标环境为 Python 3.11 / 3.12（Windows PowerShell 示例）：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
```

macOS / Linux 把第二行换成 `source .venv/bin/activate`。

**跑一次完整报告**（使用合成数据）：

```bash
python -m research_engine.cli --data examples/synthetic_dsc.csv \
  --config examples/synthetic_config.json --out runs
```

终端会打印 `RUN_DIR` 与 `OUTPUT_BUNDLE`。进入运行目录可看到：

```text
inputs/                 本次输入副本（不可变）
manifest.json           输入哈希、引擎版本、AI 计划状态
results.json            事件结果、数据哈希
validation.json         numerical_status / 科学审查状态 / issues
figures/*.png|*.svg     全扫描曲线与积分示意图
report_draft.docx       待人工审核的 Word 草稿
run_log.json            成功、阻断或异常
download_bundle.zip     以上文件的打包
```

**启动网页**：

```bash
python -m streamlit run app.py
```

上传 `examples/synthetic_dsc.csv` 与 `examples/synthetic_config.json`，运行后先看"数值状态"，再下载 ZIP。CSV 上限 30 MB，配置上限 1 MB。

**查公式 / 单次计算**：

```bash
python -m research_engine.formula_cli list
python -m research_engine.formula_cli list --experiment DSC
python -m research_engine.formula_cli show dsc_enthalpy_time_v1
python -m research_engine.formula_cli run dsc_enthalpy_time_v1 method_registry/example_dsc_time.json
```

`run` 的返回永远带 `"status": "CALCULATED_NOT_SCIENTIFICALLY_VALIDATED"`，即使数值正确也不代表方法适用于你的样品。

**可选：启用 AI 规划**（不安装也可正常使用全部离线功能）：

```bash
python -m pip install -r requirements-ai.txt
export AI_API_KEY="..."          # 或 OPENAI_API_KEY；PowerShell 用 $env:AI_API_KEY="..."
# export AI_BASE_URL="https://..."  # 仅 HTTPS 或 localhost
python -m research_engine.plan_cli --data examples/synthetic_dsc.csv \
  --config examples/synthetic_metadata.json --model "你实际可调用的模型ID" \
  --out ai_plan_preview.json
```

规划器只写出建议，不自动执行；把审阅后的配置交给 `research_engine.cli` 再运行。详见 [方法规划器_使用手册.md](方法规划器_使用手册.md)。

## 6. 数据契约

CSV 必须恰好包含五列，且时间、温度、热流已转换为 s、degC、mW：

```csv
sample_id,segment,time_s,temperature_c,heat_flow_mw
PE_demo,H1,0,25.0,2.1
```

配置的必填结构：

| 字段 | 要求 |
|---|---|
| `dataset_type` | `synthetic` 或 `experimental` |
| `measurement_units` | 必须严格等于 `{"time_s":"s","temperature_c":"degC","heat_flow_mw":"mW"}` |
| `samples[].mass_mg` | > 0 |
| `samples[].endotherm_up` | 显式布尔值，不猜 |
| `samples[].delta_h0_j_g` | 可选；用于结晶度，必须 > 0 |
| `samples[].reference_verified` | 布尔；未核验时只出 `WARN` 并标注 |
| `samples[].cold_crystallization_excluded` | 布尔或 `null`；未评估时拒绝给出结晶度 |
| `windows[]` | `event_id / sample_id / segment / phase / start_c < end_c`，窗口 ≥21 点 |
| `baseline_fraction` | 0.03–0.20，默认 0.10 |

`phase` 只接受 `melting`、`crystallization`、`cold_crystallization`；熔融必须出现在升温段且吸热，降温结晶必须放热，冷结晶必须出现在升温段且放热。

## 7. 质量门

| 级别 | 触发条件 | 后果 |
|---|---|---|
| `FAIL` | 扫描方向与相态不符 | 不生成图与 DOCX |
| `FAIL` | 积分符号与吸热方向矛盾 | 同上 |
| `FAIL` | 扣基线后窗口内无可测峰 | 同上 |
| `FAIL` | 端点比例 5/10/15% 导致面积变化 > 25% | 同上 |
| `FAIL` | 结晶度落在 [0, 100] 之外 | 同上 |
| `WARN` | 基线敏感度 15–25% | 生成草稿，标注风险 |
| `WARN` | 参考焓由用户提供但未核验 | 结晶度标注 `unverified` |
| `WARN` | 冷结晶未评估 | 不给结晶度 |
| `WARN` | 峰贴近积分窗口边缘 | 提示复核窗口 |
| `WARN` | 合成数据 | 图表水印 + DOCX 醒目标记 |

25% 与 15% 是**工程启发式阈值**，不是 DSC 标准或统计不确定度。基线敏感度也不等于测量不确定度。

## 8. 公式注册库

`method_registry/catalog.json` 是唯一事实源。每张卡包含：表达式、输入与单位、物理前提、来源、版本、执行状态。执行器只接受**与 `inputs` 完全一致的键**，多余或缺失都会报错；不接受 `eval`/`exec`，不接受模型生成的 Python。

| ID | 实验 | 内容 | 状态 |
|---|---|---|---|
| `dsc_enthalpy_time_v1` | DSC | 沿时间积分求比焓变 | 可执行 |
| `dsc_enthalpy_temperature_v1` | DSC | 恒速温度轴积分（区分升/降温方向） | 可执行 |
| `dsc_crystallinity_v1` | DSC | 扣除冷结晶的结晶度估计 | 可执行 |
| `tga_mass_loss_v1` | TGA | 质量损失率 | 可执行 |
| `tga_t_at_loss_v1` | TGA | 指定失重率温度（T5/T10），首次交点插值 | 可执行 |
| `uv_beer_lambert_v1` | UV-Vis | Beer–Lambert 求浓度 | 可执行 |
| `ftir_transmittance_v1` | FTIR | 透过率转吸光度 | 可执行 |
| `gpc_mass_moments_v1` | GPC | 真实质量分数下的 Mn / Mw / Đ | 可执行 |
| `nmr_integral_ratio_v1` | ¹H NMR | 氢数归一化积分比 | 可执行 |
| `dsc_tg_midpoint_v1` | DSC | 玻璃化转变中点 | 仅登记 |
| `dsc_peak_deconvolution_v1` | DSC | 重叠峰分解 | 仅登记 |
| `ftir_als_baseline_v1` | FTIR/Raman | AsLS 基线 | 仅登记 |
| `tga_dtg_peak_v1` | TGA | DTG 峰值与分离 | 仅登记 |

"可执行"只表示通过基础数值单元测试，例如三角峰积分、单位换算、升降温方向、阈值插值、质量分数归一化和异常输入拒绝；**不表示方法适用于你的样品与仪器条件**。

开源选型（SciPy、pybaselines、lmfit、pyDSC、pyTGA、SpectroChemPy、nmrglue、Pint）的许可证与引入建议见 [公式注册库_使用与开源方案.md](公式注册库_使用与开源方案.md)。本项目没有复制任何第三方代码；`pyDSC` 为 GPL-3.0，仅作算法思路参考。

## 9. AI 规划器的边界

- 默认不调用任何模型；不设置密钥、不填写模型 ID 就不会联网。
- 只发送样品配置、分段统计和每段最多 32 个分箱均值点，不发送完整 CSV。
- Base URL 只允许 HTTPS 或 localhost，避免误发到明文或内网地址。
- 模型必须返回单个 JSON 对象；未知方法、编造样品、越界窗口、相态与扫描方向不符、点数不足、基线不在支持列表，全部拒绝。
- 只能使用 `dsc_peak_area_time_v1`，基线只能是 `linear_endpoint_mean` 或 `constant_endpoint_mean`。
- 方案先预览，人工勾选后再执行；`inputs/ai_plan.json` 与 SHA-256 一并留档。
- 没有任何"模型准确率"声明；v0.3 未实际调用过外部 API。

## 10. 验证记录

**v0.3 发布记录**（`RELEASE_STATUS.json`）：29 项离线测试通过，Streamlit 未实测，真实 API 未调用，真实仪器数据未测试。

**本次接手后的独立复核（2026-10-26）**：

| 检查 | 方法 | 结果 |
|---|---|---|
| Python 语法 | `py_compile` 覆盖 `app.py`、`research_engine/*.py`、`tests/*.py` | 通过 |
| 公式注册库测试 | `pytest tests/test_formula_registry.py`（12 项） | 通过 |
| 数值计算测试 | `pytest tests/test_calculations.py`（7 项） | 通过 |
| 注册库可读性 | `formula_cli list` | 13 个方法，9 可执行 / 4 仅登记 |
| 单次计算 | `formula_cli run dsc_enthalpy_time_v1 ...` | 返回 5.0 J/g，状态为未做科学验证 |
| 图形 + DOCX 端到端 | 需要 matplotlib | **未复跑**：Python 3.14 / aarch64 无可用 wheel |
| Streamlit 界面 | 需要 streamlit | **未复跑**：依赖未安装 |
| 真实 API / 真实数据 | — | **未测试** |

因此：29 项是发布记录，本次实跑的是其中 19 项（12 + 7），全部通过；图形、DOCX 端到端与界面仍需在目标环境复验。

## 11. 已知限制与文档漂移

- **没有真实数据案例**：`examples/` 由脚本生成，参数与真实 PE/PET 无关，不能当作实验结果。
- **基线阈值是启发式**：25% / 15% 不是行业规范；不同仪器、峰形与窗口会改变结论。
- **无不确定度传播**：不做重复性、误差传递或统计置信区间。
- **无单位引擎**：单位只在方法契约层校验，不会自动换算 W/g、μV、% 等。
- **跨实验公式未接入流水线**：TGA / FTIR / GPC / NMR 只是独立计算器。
- **manifest 版本号未升**：`pipeline.py` 里 `engine_version` 仍写 `0.2.0`，与 v0.3 不符。
- **旧文档未同步**：`docs/QA_AND_VALIDATION.md` 仍是 v0.1 的 9 项测试描述；以 `RELEASE_STATUS.json`、`tests/` 和本文件第 10 节为准。v0.1–v0.3 的原始变更记录保留在 [docs/RELEASE_NOTES.md](docs/RELEASE_NOTES.md)。
- **依赖范围**：`requirements.txt` 声明 pandas `<3`；本次复核环境是 Python 3.14 + pandas 3.1，超出声明范围，测试虽通过但不代表受支持。
- **许可证**：本目录未附 LICENSE，仓库当前也未声明开源许可证；复用前请先与作者确认。

## 12. 路线图

v0.4 的计划是"先真数据，再扩实验"：

1. 用一份真实 DSC 仪器导出 + 可靠标定信息建立独立案例，复核扫描程序与端点基线；
2. 把 DSC 公式注册库与 AI 峰事件规划器统一到同一方法目录；
3. 新增 TGA 正式解析器，用第二类实验检验可迁移性；
4. 在此之前不扩展更多"看起来能用"的公式卡。

## 13. 文档索引

| 文档 | 内容 |
|---|---|
| [开始使用_5步.md](开始使用_5步.md) | 从压缩包到第一次演示 |
| [公式注册库_使用与开源方案.md](公式注册库_使用与开源方案.md) | 设计原则、开源选型、13 个方法、下一步流程 |
| [方法规划器_使用手册.md](方法规划器_使用手册.md) | AI 规划器的配置、审核与责任边界 |
| [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) | 实施方案与质量门槛 |
| [docs/ASSET_AUDIT.md](docs/ASSET_AUDIT.md) | 资产核对 |
| [docs/QA_AND_VALIDATION.md](docs/QA_AND_VALIDATION.md) | v0.1 时期的验证矩阵（已过时） |
| [docs/RELEASE_NOTES.md](docs/RELEASE_NOTES.md) | v0.1 → v0.3 变更记录 |

## 14. 使用边界

这是数据辅助与草稿工具，不是代写工具。课程或期刊禁止 AI 生成内容时，只能把它用于允许的数据处理、绘图和自查；实验条件、方法适用性、结论与署名由研究者负责。任何输出在人工审核前都不得作为最终结果提交。
