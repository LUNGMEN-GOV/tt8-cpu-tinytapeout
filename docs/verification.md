# Tiny8 CPU 验证报告

验证日期：2026-11-25（Asia/Singapore）

## 结论

RTL 功能、Verilog 结构、复位行为和 SKY130 标准单元面积估算已检查。
初版 16 字节程序存储器在官方详细布线中无法于 1x1 Tile 收敛；本版将程序
存储器压缩为 8 字节后，标准单元映射面积下降约 33.2%。优化版已通过官方
GDS、DRC/LVS、Tiny Tapeout precheck 和门级回归，确认可以保持 1x1 Tile。

## 基线

- 官方模板：`TinyTapeout/ttsky-verilog-template`
- 模板提交：`a42e6662fab316e93b4e26399e21d41664a460b7`
- 模板 workflow：`TinyTapeout/tt-gds-action@ttsky26d`
- 顶层：`tt_um_lungmen_gov_tt8_cpu`
- 请求面积：`1x1` Tile
- 目标时钟：10 MHz，`CLOCK_PERIOD=100 ns`
- 布局目标密度：70%

## RTL 仿真

工具：

- Icarus Verilog 13.0 stable
- Cocotb 2.1.0
- Python 3.13

结果：`TESTS=4 PASS=4 FAIL=0 SKIP=0`。

| 用例 | 覆盖内容 | 结果 |
|---|---|---|
| `test_reset_loader_and_arithmetic_logic` | 同步复位、装载、LDI、ADD、SUB、全部逻辑/移位、HALT | PASS |
| `test_jumps_and_flags` | JZ taken、JNZ taken/not-taken、JMP、Z 标志 | PASS |
| `test_input_move_step_and_enable` | IN、MOV、STEP、`ena` 暂停和输出隔离 | PASS |
| `test_restart_preserves_program_and_reset_erases_it` | START 保留程序重跑、`rst_n` 擦程序和状态 | PASS |

测试入口：

```sh
cd test
make -B
```

Windows 可执行 `python run.py`。

## 汇编器

`tools/test_assembler.py`：`Ran 4 tests ... OK`，覆盖示例编码、标签、
全部操作数格式、超出 8 字节程序和超出 3 位跳转地址时的拒绝逻辑。

## 结构和复位检查

Yosys 0.71 读取 Verilog-2005、展开 process 并执行 `check`：

- 顶层和子模块解析成功；
- `Found and reported 0 problems`；
- 没有推断锁存器；
- 单一 `clk` 时钟域，无门控时钟；
- 低有效复位只在 `posedge clk` 采样，为同步复位；
- 复位清 R0-R3、PC、标志、装载地址、HALTED 和全部 8 个程序字节；
- `START` 清 CPU 状态但不写程序存储器。

## 初版官方布局布线结果

GitHub Actions `GDS` run `45588310122` 对 16 字节版本完成了综合、放置和
全局布线，但详细布线持续存在约一万处违例，因确定无法收敛而停止：

- 放置单元面积：15,648.4309 µm²；
- 可用自由面积：15,919.0176 µm²；
- 最低可行密度：84.0%，高于配置的 70%；
- 为改善可布线性，流程将原始 13,216.18 µm² 单元面积膨胀 18.4%；
- 全局布线完成但报告拥塞；
- 详细布线违例：迭代 0 为 11,150，迭代 1 为 12,004，迭代 2 仍为
  10,146；后续迭代没有形成收敛趋势；
- 放置后建立时间无违例，但保持时间修复前有 138 个违例端点；流程未完成，
  因此没有可作为签核依据的 post-route 时序结果。

结论是 16 字节版本不适合继续以 1x1 提交，而不是增加 Tile。为尽可能降低
流片成本，本版保留完整指令集和 10 MHz 目标，仅将程序容量改为 8 字节。

## 优化版面积估算

通用 Yosys 综合：

- 107 个触发器；
- 840 个通用原始单元；
- `check`：`Found and reported 0 problems`。

使用 `sky130_fd_sc_hd__tt_025C_1v80.lib` 做标准单元映射：

- 映射单元数：689；
- 标准单元面积总和：**7,011.7248 µm²**；
- 其中时序单元：3,102.9760 µm²（44.25%）。

相对初版的本地同工具映射结果，面积由 10,498.8192 降至 7,011.7248 µm²
（−33.2%），映射单元由 958 降至 689（−28.1%），触发器由 174 降至
107（−38.5%）。模板标注单 Tile 约为 167x108 µm，即毛面积 18,036 µm²；
当前映射单元面积约占毛面积 38.9%。该比例不包含布线、tap/filler/decap、
时钟树、边界和拥塞影响，因此仍不能视为已完成布局。

## 优化版官方 GDS 结果

GitHub Actions `GDS` run `45606454765`（提交 `ef67b0b`）在 4 分 44 秒内
完成布局布线，随后门级测试、precheck 和版图 viewer 均通过：

- 官方综合标准单元面积：8,445.6000 µm²；
- post-route 标准单元面积：10,636.5 µm²；
- core 面积：16,493.3 µm²，标准单元利用率：64.4895%；
- 详细布线最终违例：0；Magic DRC：0；LVS：0；天线：0；供电网格：0；
- post-route setup 最差余量：56.4307 ns，违例数 0，TNS 0；
- post-route hold 最差余量：0.1342 ns，违例数 0，TNS 0；
- 门级 Cocotb 回归、Tiny Tapeout precheck 的 17 项检查及 viewer 部署通过。

最终指标还记录了 251 个 max-slew 和 1 个 max-fanout 告警（max-cap 为 0）。
LibreLane 将 max-slew 标为 warning，而不是 setup/hold 或制造性失败；官方 GDS
workflow 仍判定成功。鉴于 10 MHz 的 setup/hold 余量充足，继续增加缓冲会
提高面积和布线成本，本版不为消除非致命告警而扩大 Tile。流片前若 shuttle
更新 PDK 或 flow 版本，应重新运行 workflow，不能沿用本报告的数值。

## 时序检查

设计约束已统一为 10 MHz / 100 ns。RTL 只有一个时钟域，所有运算为
8 位组合逻辑，没有门控时钟或跨时钟域。Yosys/ABC 已完成 SKY130 单元映射，
但本地轻量工具链不能对该 Liberty 的参数化单元完成可靠的签核 STA，因此
这里**不声称已通过布局后时序**。

100 ns 周期相对 8 位 ALU 是保守目标。优化版 post-route setup/hold 余量均
为正且 TNS 为 0，支持 10 MHz 约束。这里的“通过”是该 flow/PDK/角点下的
静态时序结果，不是对任意电压、温度、封装和实验条件的绝对硅后保证。

## 官方流程状态与硅后范围

- RTL test：通过；
- LibreLane 1x1 GDS：通过；
- post-route setup/hold：通过；
- DRC、LVS、天线、供电网格：通过；
- Tiny Tapeout precheck：通过；
- 生成的门级网表 Cocotb 4/4 回归：通过；
- viewer：通过。

仍需在收到实体 DevKit 后验证实际硅片的功能、最高频率、电压和温度范围；
布局前检查无法替代硅后测试。
