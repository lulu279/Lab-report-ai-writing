# 合成测试数据（不是实验数据）

`synthetic_dsc.csv` / `synthetic_config.json` 是 `scripts/create_synthetic_fixture.py` 通过不同温度轴的线性基线与高斯吸热/放热峰生成，用于验证数据解析、单位换算、积分、符号、绘图和文件输出。

这套数据未经 DSC 仪器采集，也并非对用户历史 DSC 结果的数字化还原。严禁将它作为真实材料性能或课程作业实验结果。

生成新样例：

```bash
python scripts/create_synthetic_fixture.py
```
