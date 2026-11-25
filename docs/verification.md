# Tiny8 CPU 验证报告

验证日期：2026-11-25（Asia/Singapore）

## 结论

RTL 功能、Verilog 结构、复位行为和 SKY130 标准单元面积估算已检查。
当前结果支持继续使用 1x1 Tile，但**尚不能替代官方布局布线、签核 STA、
DRC/LVS、precheck 和门级回归**。提交前必须让仓库自带的 Tiny Tapeout
GitHub Actions 全部通过。

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

`tools/test_assembler.py`：`Ran 3 tests ... OK`，覆盖示例编码、标签、
全部操作数格式和超出 16 字节时的拒绝逻辑。

## 结构和复位检查

Yosys 0.71 读取 Verilog-2005、展开 process 并执行 `check`：

- 顶层和子模块解析成功；
- `Found and reported 0 problems`；
- 没有推断锁存器；
- 单一 `clk` 时钟域，无门控时钟；
- 低有效复位只在 `posedge clk` 采样，为同步复位；
- 复位清 R0-R3、PC、标志、装载地址、HALTED 和全部 16 个程序字节；
- `START` 清 CPU 状态但不写程序存储器。

## 面积估算

通用 Yosys 综合：

- 174 个触发器；
- 1122 个通用原始单元。

使用 `sky130_fd_sc_hd__tt_025C_1v80.lib` 做标准单元映射：

- 映射单元数：958；
- 标准单元面积总和：**10,498.8192 µm²**；
- 其中时序单元：5,084.8768 µm²（48.43%）。

模板标注单 Tile 约为 167x108 µm，即毛面积 18,036 µm²。映射单元面积
约占毛面积 58.2%。该比例不包含布线、tap/filler/decap、时钟树、边界和
拥塞影响，因此不能视为已完成布局；`PL_TARGET_DENSITY_PCT=70` 是为
1x1 Tile 收敛设置的起点。

## 时序检查

设计约束已统一为 10 MHz / 100 ns。RTL 只有一个时钟域，所有运算为
8 位组合逻辑，没有门控时钟或跨时钟域。Yosys/ABC 已完成 SKY130 单元映射，
但本地轻量工具链不能对该 Liberty 的参数化单元完成可靠的签核 STA，因此
这里**不声称已通过布局后时序**。

100 ns 周期相对 8 位 ALU 是保守目标。最终必须以官方 GDS workflow 的
post-route setup/hold 报告为准；若出现负裕量，先保持 1x1 Tile 并进一步
增大 `CLOCK_PERIOD`，不要直接购买更多 Tile。

## 尚待官方流程确认

- LibreLane 完整布局布线是否在 1x1 Tile 收敛；
- post-route setup/hold slack；
- 拥塞和天线修复；
- DRC、LVS、Tiny Tapeout precheck；
- 生成的门级网表 Cocotb 4/4 回归；
- 实际硅片频率、电压和温度范围。

这些检查由模板中的 `.github/workflows/gds.yaml` 在推送到 GitHub 后执行。
