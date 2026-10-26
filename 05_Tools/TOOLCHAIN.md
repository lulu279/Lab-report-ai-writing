# 工具链（TOOLCHAIN）

版本：1.1（2026-10-26）
适用：本工作系统的实验数据处理、绘图、DOCX/XLSX/Origin 生成与校验。
原则：只用已确认可用的工具；不假设 Linux 包管理器；不把“代码无报错”当作“文件已验证”。

## 1. 运行环境（2026-10-26 实测）

| 层 | 现状 | 用途 |
|---|---|---|
| 宿主机（qoder_bridge） | Python 3.14.7、Node 26.8.1、git 2.55；Harmonybrew PATH | 跑报告生成器/检查脚本 |
| 宿主机 Python 标准库 | `zipfile`、`xml.etree`、`struct`、`zlib`、`csv`、`json`、`re` 可用 | DOCX/XLSX 结构检查、文本提取 |
| 宿主机 Python 包 | `openpyxl 3.1.5`、`pypdf 6.21.x` 可用；**无** `python-docx`、`numpy`、`pandas`、`matplotlib`、`scipy` | XLSX、PDF 页数；不要假设科学计算栈存在 |
| C 扩展 | `lxml.etree`、`PIL._imaging`、numpy 的 `.so` 可能因权限被拒载 | 不要依赖；改用标准库或 GUI |
| 文档转换 | 命令行无 `soffice`/`libreoffice`/`pandoc`/WPS | PDF 由用户在 Word/WPS 导出 |
| Qoder 沙箱 `python3` | Skulpt shim；无 `zipfile`，不支持 `nonlocal` | **不要**用它跑 `build_report_docx.py` |
| 历史脚本 | 依赖 numpy/pandas/matplotlib/scipy/python-docx/lxml/PyMuPDF/Pillow/nmrglue/originpro/pywin32 | 只在原 Windows/Origin 环境运行；当前宿主未重跑 |

> 结论：报告 DOCX 由 `05_Tools/build_report_docx.py`（纯标准库）生成；PDF 需在 Word/WPS 中从最终 DOCX 导出；科学绘图优先用 Origin/Excel GUI 或已有 PNG/SVG，不要声称用 matplotlib 重跑过。
> 不确定该用哪个 `python3` 时，先读 `05_Tools/RUN_PYTHON.md`：沙箱 Skulpt 不能跑；用宿主机 CPython 3.10+ 或 qoder_bridge。

## 2. 各环节推荐工具

| 环节 | 首选 | 备选 | 说明 |
|---|---|---|---|
| 原始数据解析 | Python 标准库 `csv`/`json` | Excel/WPS | 先核对列/单位；原始只读 |
| 峰检测/积分 | Origin/Excel GUI + 手工记录参数 | 自写纯 Python 算法 | 当前无 scipy；算法与参数写入交付说明 |
| 拟合 | Excel LINEST/规划求解 | 自写最小二乘（纯 Python） | 给参数±标准误、R²、n、残差 |
| 科学绘图 | Origin / Excel / 已有 PNG/SVG | Node 纯 JS 绘图（需自装） | 当前 CLI 无 matplotlib/pureimage；不要声称已脚本绘图；见 `FIGURES.md` |
| DOCX 报告 | `05_Tools/build_report_docx.py` | Word/WPS 模板手工排版 | 纯标准库；封面/标题/图/表/页码 |
| DOCX 文本读取 | `05_Tools/docx_text.py` | `unzip -p` + XML | 读范例、查正文、做统计 |
| XLSX | `openpyxl`（宿主 Python） | Excel/WPS | 原生图表、公式、三线表 |
| PDF 检查 | `pypdf` + `05_Tools/pdf_text.py` | 人工逐页 | 页数、文本；不替代渲染 |
| 字体审计 | 解压 DOCX + XML 检查 | Word 字体替换 | `rFonts` 显式率、主题引用 |
| 图片检查 | `struct` 读 PNG/JPEG 头 | 人工 | 尺寸/比例；不依赖 Pillow |
| 旧值污染 | `05_Tools/check_contamination.sh` | 人工核对 | 命中不等于错误，必须逐条确认 |
| DOCX 元数据 | `05_Tools/sanitize_docx_meta.py` | 手工改 core.xml | 收录历史范例前去掉姓名/作者 |
| 版本管理 | 目录/文件命名 + CHANGELOG | Git | 不覆盖；旧版入 99_Archive/ |

## 3. 依赖与安装原则

- 先检查已装：`python3 -c "import x"`；不要在未确认时假设可用。
- 缺包时优先用标准库；需要 C 扩展的包（numpy/lxml/Pillow）在当前宿主可能因 `.so` 权限失败，不要反复重装。
- XLSX 可用 `openpyxl`；DOCX 不要依赖 `python-docx`。
- 需要绘图时，优先用 Origin/Excel GUI 生成 PNG/SVG，再交给报告生成器；不要在交付说明里写“已用 matplotlib 重跑”。
- 不在交付文档中写“pip install 即可”，除非实际验证过。

## 4. 报告 DOCX 生成

```bash
# 1) 写 report.md（front matter + 正文 + 图 + 表）
# 2) 生成（封面字段不齐会报错；草稿用 --draft）
python3 05_Tools/build_report_docx.py report.md --out report.docx
python3 05_Tools/build_report_docx.py report.md --out report_draft.docx --draft

# 3) 结构审计
python3 05_Tools/build_report_docx.py --audit report.docx

# 4) 旧范例数值污染检查
sh 05_Tools/check_contamination.sh report.docx

# 5) 在 Word/WPS 打开 → 导出 PDF → 逐页检查

# 读讲义/PDF 文本（pypdf，宿主机可用）
python3 05_Tools/pdf_text.py 00_START/COURSE_HANDOUT_2026.pdf --pages 1-10
```

- `build_report_docx.py` 的语法与 front matter 说明见文件头。
- 它设置：A4、2.20/2.15/2.00/2.35 cm、宋体+Times、正文 10.5 pt/1.5 倍/首行缩进 2 字符、一级/二级标题 12 pt、图注/表注 9 pt、三线表、页码、页眉。
- 不支持：原生 Word 公式（OMML）、自动图/表编号、目录。公式以居中斜体文本呈现；编号需在 Markdown 中手写。
- `build_delivery_docx.py` **只**用于生成 `00_交付文档.docx`，不是报告生成器；不要拿它当报告模板。

## 5. XLSX 生成要点

- `openpyxl` 写数据/公式/样式/原生图。
- 图表必须挂到 worksheet，保留数据引用；不要只插图片。
- 公式写入后，用 Excel/WPS 打开重算；检查 `#REF!`。
- 三线表样式；表头单位；冻结首行。
- 工作表命名与脚本/报告一致。
- 原生 chart part 可能在 `xl/charts/` 或 `xl/drawings/charts/`；统计时两处都查。

## 6. Origin 要点

- 目标版本内嵌 Python + originpro；不要假设新接口。
- 基础接口优先；格式属性 `try/except`。
- 一次一个脚本；结束确认 `Origin64.exe` 退出。
- `draw -l` 在 Origin 2021 可能不落图；标注用文本对象。
- `.opju` 必须实际打开验证；只有脚本 → 写“仅语法/兼容性检查”。

## 7. 环境边界（必须如实写）

| 事项 | 当前能否做 | 交付说明写法 |
|---|---|---|
| 生成 DOCX | 可（`build_report_docx.py`，宿主 Python） | “已生成；已做结构审计” |
| 打开 DOCX/XLSX | 可（Word/WPS 或 XML 检查） | “已打开/已做 XML 检查” |
| 渲染 PDF | 需 Word/WPS；命令行不可 | “已逐页检查”或“未渲染” |
| 重跑 numpy/matplotlib 脚本 | 当前宿主不可（缺包/`.so` 权限） | “未在本机重跑；脚本来自原环境” |
| 运行 Origin | 当前宿主不可 | “仅静态语法检查，需在 Origin 2021 验证” |
| 统计 DOCX 图/表/字体 | 可（zip+XML） | “已统计” |
| 统计 XLSX 原生图 | 可（zip+XML） | “已统计 chart part” |

## 8. 最小工具集（推荐保留）

```text
Python 3.10+（真实 CPython，不是 Skulpt shim）
  stdlib: zipfile, xml.etree, struct, zlib, json, csv, re
  openpyxl（XLSX）
  pypdf（PDF 页数/文本）
unzip（读 DOCX 包）
Word/WPS（打开/渲染/导出 PDF）
Excel/WPS（打开/重算/看图）
Origin 2021（如课程要求）
```

不需要为了“工具齐全”安装大量包；能完成“数据—图—文档—校验”即可。
