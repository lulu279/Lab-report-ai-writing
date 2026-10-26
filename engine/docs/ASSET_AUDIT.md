# 已有资产、可复用程度及缺失清单

核对依据：用户上传 `科研AI工作系统.zip`，以及 `DSC_PE_PET_高分子物理实验报告.docx`。

## 实际存在的内容

- 科研系统含 35 份 Markdown、1 个 DOCX、1 个 Python 脚本 `05_Tools/build_delivery_docx.py`。
- 存在 `STYLE_PROFILE.md`、`FORMAT_PROFILE.md`、`SCIENTIFIC_INTEGRITY.md`、`SOURCE_POLICY.md`、`EXPERIMENT_REPORT.md`、`DATA_FIGURE_DELIVERY.md`、`SCRIPT_INDEX.md`、`KNOWN_ISSUES.md`。
- DSC 正式 DOCX 为一份历史报告，包含 PE、PET 的两次升降温循环及多幅图表和相变焓结果；**历史报告只作为文字风格与分析结构参考，不作为本原型计算输入**。
- 复制到 `knowledge/source_rules/` 的文件仅供人工参考；真正用于可选 AI 写作的提示词只有 `knowledge/ACTIVE_STYLE.md`，不读取历史 DSC 数值。

## 脚本索引中提到但本次 ZIP 不含实体的 DSC 脚本

`analyze.py`、`compute.py`、`figdata.py`、`make_excel.py`、`makefigs.js`、`make_figs_v2.py`、`make_report.py`、`report_content.py`、`build_opj.py`、`final_verify.py`。这些名称仅来自索引；**未假设这些代码已经恢复或通过测试**。

## 当前尚未取得的关键材料

1. 原始 PE/PET DSC 仪器导出文件（TXT/CSV 等）；
2. 数据字段/单位、热流符号、时间戳的真实定义；
3. 样品编号、扫描段起止时刻、保温段和扫描速率；
4. 原始积分窗口、基线锚点及其人工审核记录；
5. 独立可核验的参考熔融焓来源与冷结晶处理说明；
6. 经授权的课程模板、写作要求和实验实际操作记录；
7. Origin 2021 运行环境与原始项目；
8. 具有未见结果的新任务测试集。

## 当前原型明确没有的能力

- 不能自动解析任意 Mettler Toledo TXT 格式，也不能从报告图片恢复可信原始数据；
- 不能从曲线自动可靠区分熔融、结晶、玻璃化、冷结晶，必须显式给段与窗口；
- 尚不计算 Tg，不进行仪器热流标定；
- 未实现 XLSX/Origin 工程生成，不声称输出 `.opju`；
- 不自动生成 PDF，需本地 Word/LibreOffice 转换与逐页核验；
- 仅有基础数值防错检查，不代表实验机理被独立验证；
- 不自动填写课程报告缺失的操作步骤/参考文献/身份信息；
- Streamlit 界面是否在用户目标机器正常运行，需要在 Windows 环境安装并实测。
