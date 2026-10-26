# 用哪个 Python 跑生成器（RUN_PYTHON）

`build_report_docx.py` 只用 Python 标准库，**任何 CPython 3.10+ 都能跑**。问题不在脚本，而在“你当前拿到的是哪个 python3”。

## 1. 先自检

```bash
python3 -c "import zipfile, sys; print(sys.version); print('OK')"
```

- 输出 `3.10`–`3.14` 且 `OK`：可以直接跑。
- 输出 `qoder-sandbox python3: Skulpt subset` 或 `NotImplementedError: zipfile`：这是 Qoder 沙箱的 Skulpt shim，**不能跑生成器**。换真实 CPython。

## 2. 三种可用入口

### A. Qoder 桌面 + qoder_bridge（本系统实测）

宿主机 Python 3.14.7 可通过 `qoder_bridge` 的 `exec` 调用。让 agent 执行：

```text
工具：mcp__qoder_bridge__exec
cwd：<本系统目录>
cmd：python3 05_Tools/build_report_docx.py report.md --out report.docx
```

先跑一次：

```text
cmd：python3 -c "import zipfile, sys; print(sys.version); print('OK')"
```

### B. 本机终端（macOS/Linux/Windows）

在系统终端里确认 `python3` 是 CPython 3.10+，然后：

```bash
cd <本系统目录>
python3 05_Tools/build_report_docx.py report.md --out report.docx
```

### C. 没有 Python 3.10+ 的机器

- 不要用 Qoder 沙箱的 Skulpt shim 硬跑；
- 不要在交付说明里写“已生成 DOCX”；
- 把 `report.md`、图片、表格交给用户，在 Word/WPS 中手工排版，或先安装 CPython 3.10+。

## 3. 生成后

```bash
python3 05_Tools/build_report_docx.py --audit report.docx
sh 05_Tools/check_contamination.sh report.docx
```

PDF 仍需在 Word/WPS 中从最终 DOCX 导出；未导出就写“未渲染/未验证”。

## 4. 为什么不在沙箱里装包

- 沙箱 `python3` 是 Skulpt，不是 CPython；`pip install` 不适用。
- 沙箱里的 C 扩展 `.so` 可能被拒载（lxml/Pillow/numpy 都遇到过）。
- 生成器刻意只用标准库，就是为了绕开这些依赖；换成真实 CPython 即可。
