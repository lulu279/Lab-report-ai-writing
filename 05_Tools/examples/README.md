# 报告生成器示例（examples/）

这是一份**合成烟雾测试**，不是实验报告，也不含任何真实实验数据。

## 文件

- `sample_report.md`：front matter + 标题 + 正文 + 图 + 表 + 公式 + 列表 + 参考文献。
- `sample_fig.png`：合成曲线（900×520），由 `make_sample_fig.py` 用纯标准库重新生成（无中文字体，仅验证嵌图）。
- `make_sample_fig.py`：生成上面 PNG 的脚本；不是科学绘图工具，不替代 Origin/Excel。
- `sample_report.docx`：生成结果。

## 运行

```bash
# 用真实 CPython 3.10+（不要用 Qoder 沙箱的 Skulpt shim）
cd 05_Tools/examples && python3 make_sample_fig.py && cd ../..
python3 05_Tools/build_report_docx.py 05_Tools/examples/sample_report.md \
  --out 05_Tools/examples/sample_report.docx

# 结构审计
python3 05_Tools/build_report_docx.py --audit 05_Tools/examples/sample_report.docx

# 污染检查（样例用的是独特值，应该通过）
sh 05_Tools/check_contamination.sh 05_Tools/examples/sample_report.docx
```

## 检查点

- 封面：标题、实验名、班级/姓名/学号/组别/日期。
- 标题：12 pt 加粗；正文 10.5 pt、1.5 倍、首行缩进。
- 图片：嵌入 PNG，宽 ≤15 cm；图注 9 pt 居中。
- 表格：三线表、表头重复、表题在上。
- 公式：居中斜体文本（不是 OMML）。
- 页码：页脚 PAGE/NUMPAGES 域；封面不显示。
- 参考文献：9 pt 悬挂缩进。

## 注意

- 样例中的姓名/学号是虚构的；真实报告必须由学生填 `00_START/COVER_FIELDS.md`。
- 样例中的数值是合成的；不要复制到真实报告。
- 未在 Word/WPS 中逐页渲染；打开后请检查分页、图注、表格跨页和字体。
