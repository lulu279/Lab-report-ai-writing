# Research DSC Engine v0.3：可审计的科学公式注册库

在 v0.2 基础上增加 `method_registry/catalog.json`、`research_engine/formula_registry.py` 和 `research_engine/formula_cli.py`，并在 Streamlit 页底增加方法查阅和安全计算演示。

**9 个方法有基础数值测试；4 个方法只登记不可执行。** 新增方法库涵盖 DSC、TGA、UV-Vis、FTIR、GPC 与 NMR 的基础公式，不代表其他实验的完整自动处理流水线已经开发。详细说明见 [公式注册库_使用与开源方案.md](公式注册库_使用与开源方案.md)。

快速验证：

```bash
python -m pytest -q
python -m research_engine.formula_cli list
python -m research_engine.formula_cli run dsc_enthalpy_time_v1 method_registry/example_dsc_time.json
python -m streamlit run app.py
```

重要限制：**真实科研实验数据没有接入，也没有真实 AI API 调用。** 新增公式的 `tested_executor` 状态仅表示基础数值测试通过，不代表特定样品、仪器及实验条件下的方法适用性被验证。

---

# Research DSC Engine v0.2（AI 参与分析方法选择）

**新增**：可选 OpenAI-compatible AI 方法规划器，能够建议 DSC 峰事件、积分窗口与已实现基线算法，用户核验批准后由 Python 执行。**没有预设或实际调用任何外部 AI 模型。**

使用方式与限制见：[方法规划器使用手册](方法规划器_使用手册.md)。上一版规范、源脚本、测试保留在本项目中。

**运行测试：** `python -m pytest -q`；**启动界面：** `python -m streamlit run app.py`；**可选安装外部 AI：** `pip install -r requirements-ai.txt`。

---

# Research DSC Engine · MVP v0.1

> 一个真正可运行、但对科学与数据边界保持审慎的 **Python + Streamlit** DSC 报告生成原型。它不是完整的实验报告代写系统，不会使用用户历史 DSC 报告的峰温、焓或结晶度进行本次计算。

## 已经实现的功能

1. 标准化、显式分段 CSV 与 JSON/YAML 参数配置读取。
2. 检查样品质量、数据单位、热流方向、扫描方向、重复/缺失数据和积分窗口。
3. 指定窗口内的端点线性基线、按测量时间积分、峰温、样品质量归一化、条件性结晶度计算。
4. 基线选择敏感度分析（不是严格统计不确定度）。
5. 每个样品的全扫描曲线、每个事件的积分示意图，输出 PNG 和 SVG。
6. 输出 `results.json`、`validation.json`、`manifest.json`（输入哈希）、运行日志和可编辑 DOCX 草稿。
7. 数值检查为 FAIL 时，**停止生成报告**；正常输出依然标注“科学未审核”。
8. 可选 API 模式只生成 **未经科学审核的讨论草稿**，不允许 AI 执行或更改积分数值。
9. Streamlit 上传/预览/打包下载界面；也支持无需 Streamlit 的命令行。
10. 自带完全独立的合成数据与 `pytest` 测试。

## 当前没有实现的功能

- **没有真实 DSC 原始数据**：历史报告的峰温和热焓仅为历史记录，不用于运行或验证。
- 不支持任意仪器专有 TXT 原始导出；没有自动列名映射/热流单位猜测，也没有自动分段。
- 不自动计算 Tg、热容台阶、校正冷结晶条件之外的其他转变或仪器标定。
- 未提供真实 Origin 2021 工程、Excel 原生图表或自动 PDF 导出。
- 未实现真正的科学机理审核；文档中的分析文字属于待审阅草稿。
- 目标用户机器上的 Streamlit 界面及可选 API 调用尚需环境实测。

## 目录结构

```text
Research_DSC_Engine_MVP/
├── app.py                       # Streamlit 前端
├── requirements.txt
├── requirements-ai.txt
├── research_engine/
│   ├── schema.py                # 配置数据模型和验证
│   ├── loader.py                # CSV 严格解析
│   ├── calculations.py          # DSC 积分、峰温、结晶度、质量标记
│   ├── figures.py               # PNG / SVG
│   ├── ai.py                    # 可选、未审核 AI 讨论
│   ├── report.py                # DOCX 草稿
│   ├── pipeline.py              # 编排、溯源、阻断与打包
│   └── cli.py                   # 命令行
├── knowledge/
│   ├── ACTIVE_STYLE.md          # 安全摘录、避免盲测泄漏
│   └── source_rules/            # 原有规范只读参考
├── examples/
│   ├── synthetic_dsc.csv        # 合成测试数据，绝非实验数据
│   └── synthetic_config.json    # 明确单位、窗口、质量等
├── scripts/
│   └── create_synthetic_fixture.py
├── docs/
│   ├── IMPLEMENTATION_PLAN.md
│   ├── ASSET_AUDIT.md
│   └── QA_AND_VALIDATION.md
├── tests/
└── runs/                        # 每次执行自动产生唯一目录；不写回原文件
```

## 安装方法（Windows PowerShell）

> 请先安装 **Python 3.11 或 3.12**。下列命令属于建议的目标环境流程；本次验证环境未能安装 Streamlit（网络不可用），因此 UI 尚未在该环境实际启动。

在解压目录执行：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

PowerShell 如果阻止激活，也可以直接使用 `.venv\Scripts\python.exe` 运行命令。

### 第一次自检（无 API、无原始仪器文件）

```powershell
python -m pytest -q
python -m research_engine.cli --data examples/synthetic_dsc.csv --config examples/synthetic_config.json --out runs
```

正常情况会打印 `RUN_DIR` 和 `OUTPUT_BUNDLE`。进入该目录查看 `validation.json`、`results.json`、`report_draft.docx` 和 `figures/`。标有 `SYNTHETIC` 的内容只用于测试。

### 启动本地网页界面

```powershell
python -m streamlit run app.py
```

在浏览器打开 Streamlit 提示的本地 URL（通常为 `http://localhost:8501`），分别上传 `examples/synthetic_dsc.csv` 和 `examples/synthetic_config.json`。点击运行，读取质量提示，再下载结果 ZIP。

### 可选：启用 AI 讨论草稿

AI 是可选项，且只负责第 4 节未经审核的讨论；不用于读取历史结果或计算峰面积。需要先安装：

```powershell
python -m pip install -r requirements-ai.txt
$env:OPENAI_API_KEY="你的密钥"
python -m research_engine.cli --data examples/synthetic_dsc.csv --config examples/synthetic_config.json --out runs --ai --model "你实际可调用的模型ID"
```

可选 AI 调用会将事件结果与 ACTIVE_STYLE 摘要发送给所配置的 API。未取得数据共享许可时，不应启用该模式。未调用 API 时会明确写明 `NOT_USED`，绝不虚报已完成 AI 写作。

## 从仪器原始数据走向真实报告

**当前需要人工做一次可信转换：**

1. 保留仪器原始 TXT/CSV，不要覆盖。记录原始文件和仪器实际标定单位。
2. 从仪器文档/本次实验要求确认时间、温度、热流字段（必须已转换为 s、degC、mW）。若仪器输出为 W/g、μV 或其他单位，应先依据可靠校准信息转换，不能直接改列名。
3. 显式标识升温/降温扫描段，例如 H1/C1/H2/C2；排除或明确标识保温段。不要自动将温度小波动当成阶段转换。
4. 输出 CSV 五列：`sample_id,segment,time_s,temperature_c,heat_flow_mw`。
5. 在配置中填写实际样品质量、热流吸热方向、积分窗口以及参考焓的来源与核验状态。
6. 配置 `dataset_type: experimental`，但这**只表示你声明数据为实验数据**；并不意味着系统核验了实验真实性。
7. 运行程序，先看 `validation.json` 是否含 FAIL / WARN，再审查图表、计算、Word 和实验条件。
8. 科学解释与课程文本必须由研究者审阅、补充和承担责任。

## 质量门槛

- 输入缺关键字段、单位或样品质量：拒绝计算。
- 数据时间轴异常/关键窗口过少点：拒绝计算。
- 热流方向与峰类型不符：`FAIL`，不生成报告。
- 端点比例变化使焓值相对变动超过 25%：`FAIL`，不生成报告；15–25% 标记 WARN。这些比例是**初版暂定启发式阈值**，并非普适 DSC 标准。
- 参考焓未核验、实验条件不足、合成数据：保留 WARN，要求人工确认。
- 每次成功运行后，科学解释和目标机器排版依旧标为 `NOT_REVIEWED`。

详见 [实施方案](docs/IMPLEMENTATION_PLAN.md)、[资产核对](docs/ASSET_AUDIT.md)、[质量与验证](docs/QA_AND_VALIDATION.md)。
