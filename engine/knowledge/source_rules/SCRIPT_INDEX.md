# 脚本索引（SCRIPT_INDEX）

版本：1.0（2026-10-25）
说明：以下脚本来自历史工作区，用于复现数据处理、绘图、建表/建文档/Origin。当前宿主未重跑全部脚本；执行前先读代码、确认路径与依赖。

## 1. 通用/文档

| 脚本 | 位置 | 作用 | 备注 |
|---|---|---|---|
| `build_delivery_docx.py` | `05_Tools/` | 从 `00_交付文档.md` 生成 `00_交付文档.docx` | 仅用标准库直接写 OOXML；无 python-docx 依赖；生成后已用 mammoth 解析校验 |
| `embed_svg.py` | `DSC/DSC实验报告交付/` | 将 SVG 嵌入 DOCX | 需 python-docx/lxml；字体/兼容性需验证 |
| `embed_svg2.py` | 同上 | SVG 嵌入第二版 | 同上 |
| `replace_figs_with_svg.py` | 同上 | 用 SVG 替换 DOCX 图片 | 会改文档；先备份 |
| `strip_theme_fonts.py` | `H NMR/处理结果/` | 清除 DOCX 主题字体引用 | 字体审计用 |
| `edit_report_v2.py` | `H NMR/处理结果/` | 编辑报告第二版 | 需先读代码确认改什么 |
| `update_from_figs.py` | `H NMR/处理结果/` | 用图数据回填报告 | 核对数值来源 |

## 2. DSC

| 脚本 | 位置 | 作用 |
|---|---|---|
| `analyze.py` | `DSC/DSC报告工作区/`、`DSC/DSC实验报告交付/计算脚本/` | 解析原始 txt、分段/特征点 |
| `compute.py` | 同上 | 峰积分、ΔH/Xc 计算、`results.json` |
| `figdata.py` | 同上 | 生成绘图数据（`figs.json`） |
| `make_excel.py` | 同上 | 生成 `DSC_PE_PET_数据与图表.xlsx` |
| `makefigs.js` | `DSC/DSC报告工作区/` | Node pureimage 绘制四边框 3 pt/曲线 1.1 pt 图；200 dpi |
| `make_figs_v2.py` | `DSC/DSC实验报告交付/图表改进/` | 改进版图（PNG/SVG），峰标注/基线/Tg 中线 |
| `make_report.py` | `DSC/.../计算脚本/` | 生成 DOCX 报告 |
| `report_content.py` | 同上 | 报告正文内容/数据组织 |
| `build_opj.py` | `DSC/.../Origin项目/` | 构建 Origin `.opj`（工作簿/图页/列公式） |
| `final_verify.py` | `DSC/.../Origin项目/` | 重开 Origin 工程核对焓值/导图 |
| `fixup*.py` / `fix_*.py` | `DSC/.../图表改进/字体与内容修订脚本/` | 历史修补脚本（字体、题注、keep-next、分页等）；只作参考，不建议批量重跑 |

## 3. IR

| 脚本 | 位置 | 作用 |
|---|---|---|
| `parse_ir.py` | `IR光谱/scripts/` | 解析 JASCO txt（波数/透射率），输出 CSV |
| `analyze_ir.py` | 同上 | 平滑、峰检测、峰深、归属、相似度 |
| `make_figures.py` / `make_figures_v2.py` | 同上 | 总览/单样品/对比图；v2 为报告版 |
| `build_excel.py` | 同上 | 生成 `FTIR_第一组_数据与图表.xlsx`（含原生图） |
| `build_report.py` / `build_report_v2.py` | 同上 | 生成 DOCX；v2 为宋体/Times/三线表版 |
| `红外光谱第一组_Origin脚本.py` | `IR光谱/scripts/` | 生成 `.opju`（6 工作簿 + 图页） |

## 4. TGA

| 脚本 | 位置 | 作用 |
|---|---|---|
| `process_tga.py` | `TGA/scripts/` | 解析 TG/DTG，分段/归一化 |
| `make_figures.py` | 同上 | TG/DTG、切线法、对比图 |
| `build_excel.py` | 同上 | 生成 Excel（当前工作区未保留成品 xlsx） |
| `build_report.py` / `build_merged_report.py` | 同上 | 生成/合并 DOCX |
| `make_origin_templates.py` | 同上 | 生成 Origin 模板/数据 |
| `run_origin_driver.py` | 同上 | 驱动 Origin 生成工程 |
| `TGA第一组_Origin脚本.py` | `TGA/` | Origin 工程脚本 |

## 5. NMR

| 脚本 | 位置 | 作用 |
|---|---|---|
| `process_nmr.py` | `H NMR/处理结果/` | 解析 mnova/ASCII，相位/基线/参考 |
| `analyze_all.py` | 同上 | 批量峰/积分/归属分析 |
| `final_spectra.py` | 同上 | 生成最终谱图 |
| `gen_report_final.py` | 同上 | 生成最终 DOCX |
| `gen_report_framework.py` | 同上 | 生成框架 DOCX |
| `gen_guide.py` | 同上 | 生成 MestReNova 操作指南 |
| `edit_report_v2.py` / `update_from_figs.py` | 同上 | 报告编辑/回填 |
| `strip_theme_fonts.py` | 同上 | 清除主题字体 |

## 6. GPC

| 脚本 | 位置 | 作用 |
|---|---|---|
| `build_report.py` | `GPC/work/` | 生成 DOCX/报告页 |
| `make_svg.py` | `GPC/work/` | 生成淋洗/标定/分布 SVG |
| `rewrite_conclusion.py` | `GPC/work/` | 重写结论段 |

## 7. 光致荧光

| 脚本 | 位置 | 作用 |
|---|---|---|
| `analyze.py` | `光致荧光光谱/work/` | 解析光谱、峰位/强度 |
| `results.py` | 同上 | 汇总结果 `results.json` |
| `plot_figs.py` | 同上 | 生成 6 张报告图 |
| `build_excel.py` / `build_excel2.py` | 同上 | 生成 `光致荧光光谱_数据与图表.xlsx` |
| `build_docx.py` / `build_docx2.py` | 同上 | 生成 DOCX |
| `光致荧光光谱_Origin脚本.py` | `光致荧光光谱/` | Origin 工程脚本 |

## 8. UV-Vis

| 脚本 | 位置 | 作用 |
|---|---|---|
| `UV-Vis_第一组_Origin兼容版脚本(1).py` | `UV-Vis/` | 生成 Origin 工程（兼容版） |

> UV-Vis 的拟合/绘图脚本未见单独 `.py`；结果在 `第一组_UV-Vis光谱与Beer-Lambert拟合.xlsx` 与 Origin 工程中。若需复现，先找回原始 CSV，再补脚本。

## 9. 偏光显微镜

- 当前无独立处理脚本；尺寸测量在 xlsx（`PP球晶测量`、`PHB晶粒测量`、`截线法原始数据`）中，图在 DOCX。

## 10. 中间目录

| 目录 | 性质 | 处理 |
|---|---|---|
| `IR光谱/_work/` | 探针、页面渲染、检查、旧报告 | 不交付；确认后可删/归档 |
| `GPC/work/` | 中间稿、旧版、渲染页 | 只保留最终成品与源数据；其余归档 |
| `DSC/DSC报告工作区/` | 旧工作区（含 node_modules、旧 DOCX） | 归档；不作为交付 |
| `光致荧光光谱/work/` | 中间稿、预览、备份 | 归档；不作为交付 |
| `H NMR/处理结果/QA` | 质量检查 | 保留作证据 |
| `TGA/__pycache__`、`IR光谱/scripts/__pycache__` | 缓存 | 可删 |

## 11. 使用脚本的检查顺序

1. 读脚本头部：输入路径、输出路径、依赖、参数区。
2. 确认原始数据存在；路径改为当前实际路径。
3. 先跑“解析/计算”，核对中间 CSV/JSON。
4. 再跑“绘图/建表/建文档”。
5. 打开输出文件，逐项核对；不要只看脚本 exit 0。
6. 记录运行环境、版本、日期、未验证项。
