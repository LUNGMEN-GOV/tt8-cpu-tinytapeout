# Tiny8 CPU 使用说明

## 1. 设计目标

Tiny8 是面向 Tiny Tapeout 最小 1x1 Tile 的 8 位教学 CPU。为了降低面积和
流片 Tile 成本，设计采用 8 字节程序空间、4 个寄存器、单周期 ALU，不包含
乘法器、堆栈、数据 RAM 或宽地址总线。程序由外部控制器在复位后逐字节装载。

当前项目基于 Tiny Tapeout 官方 `ttsky-verilog-template`，模板提交基线为
`a42e6662fab316e93b4e26399e21d41664a460b7`，workflow 目标为
`ttsky26d` / SKY130。若改投 IHP 或 GF180 shuttle，应从相应官方模板迁移，
不能直接复用工艺相关 workflow。

## 2. 体系结构

| 项目 | 规格 |
|---|---|
| 数据宽度 | 8 位 |
| 通用寄存器 | R0-R3，共 4 个 |
| 程序空间 | 8x8 位，可写、复位清零 |
| 程序计数器 | 3 位，地址按模 8 回绕 |
| 标志 | Z（零）、C（进位/减法无借位） |
| 执行 | 除 LDI 取两个程序字节外，每条指令一次时钟更新状态 |
| 复位 | `rst_n` 低有效同步复位 |

C 标志保留在内部供 ALU 使用和后续扩展；为节省引脚，芯片外只输出 Z。

## 3. 引脚

| Tiny Tapeout 信号 | 方向 | 功能 |
|---|---|---|
| `ui_in[7:0]` | 输入 | 程序写入字节；IN 指令执行时为外部输入数据 |
| `uo_out[7:0]` | 输出 | `REGISTER_SELECT` 选择的寄存器值 |
| `uio[0]` | 输入 | `PROGRAM_WRITE`，每个上升沿写一个字节 |
| `uio[1]` | 输入 | `START`，清 CPU 状态并从地址 0 启动，不擦程序 |
| `uio[2]` | 输入 | `STEP`，执行一条指令 |
| `uio[3]` | 输入 | `RUN`，每个上升沿执行一条指令 |
| `uio[5:4]` | 输入 | 00/01/10/11 选择 R0/R1/R2/R3 |
| `uio[6]` | 输出 | Z 标志 |
| `uio[7]` | 输出 | HALTED 状态 |
| `clk` | 输入 | 系统时钟，目标 10 MHz |
| `rst_n` | 输入 | 低有效同步复位 |
| `ena` | 输入 | 低时暂停 CPU，并清外部输出及输出使能 |

控制同时有效时优先级为 `PROGRAM_WRITE > START > RUN/STEP`。

## 4. 指令集

通用格式为 `opcode[7:4] | Rd[3:2] | Rs[1:0]`。R0-R3 编码为 0-3。

| Opcode | 助记符 | 长度 | 作用 |
|---|---|---:|---|
| 0 | `NOP` | 1 | 无操作 |
| 1 | `LDI Rd, imm8` | 2 | 下一字节装入 Rd；更新 Z，清 C |
| 2 | `MOV Rd, Rs` | 1 | Rs 复制到 Rd；更新 Z，清 C |
| 3 | `ADD Rd, Rs` | 1 | Rd = Rd + Rs；更新 Z/C |
| 4 | `SUB Rd, Rs` | 1 | Rd = Rd - Rs；C=1 表示无借位 |
| 5 | `AND Rd, Rs` | 1 | 按位与；更新 Z，清 C |
| 6 | `OR Rd, Rs` | 1 | 按位或；更新 Z，清 C |
| 7 | `XOR Rd, Rs` | 1 | 按位异或；更新 Z，清 C |
| 8 | `NOT Rd` | 1 | 按位取反；更新 Z，清 C |
| 9 | `SHL Rd` | 1 | 左移；原 bit7 进入 C |
| A | `SHR Rd` | 1 | 逻辑右移；原 bit0 进入 C |
| B | `JMP addr3` | 1 | 无条件绝对跳转 |
| C | `JZ addr3` | 1 | Z=1 时绝对跳转 |
| D | `JNZ addr3` | 1 | Z=0 时绝对跳转 |
| E | `IN Rd` | 1 | `ui_in` 装入 Rd；更新 Z，清 C |
| F | `HALT` | 1 | 停止执行，保持 PC |

## 5. 装载和执行

1. 置 `ena=1`，保持 `rst_n=0` 至少一个上升沿，然后拉高。
2. 依次将程序字节放到 `ui_in`，每个字节保持 `PROGRAM_WRITE=1` 一个上升沿。
3. 拉低 `PROGRAM_WRITE`，保持 `START=1` 一个上升沿。
4. 连续运行用 `RUN=1`；调试时每次脉冲 `STEP`。
5. `HALTED=1` 后选择 R0-R3，从 `uo_out` 读结果。
6. 脉冲 `START` 可重跑；不要用 `rst_n` 重跑，因为复位会擦除程序。

例程 `examples/demo.asm` 的字节是 `10 05 14 03 31 F0`，运行后 R0=08。

## 6. 面积、时序和成本策略

- `info.yaml` 请求最小 `1x1` Tile，直接限制数字项目的面积/成本档位。
- 10 MHz 是保守目标，为 8 位组合 ALU 和寄存器阵列预留时序裕量。
- 8 字节程序存储用触发器实现，避免工艺相关 SRAM 宏和额外 Tile；该容量是
  官方详细布线显示 16 字节版本不可布通后，为保住 1x1 Tile 费用所做的取舍。
- 所有状态都在单一时钟域；没有门控时钟、锁存器或跨时钟域。
- 最终面积、拥塞、建立/保持时间、DRC/LVS 和功耗必须以目标 shuttle 的
  官方 GDS workflow 为准。

截至 2026-11-25，Tiny Tapeout 官方计算器的数字设计价格为每 Tile 70 欧元。
本项目保持 1x1 后，单纯设计入片费用约 70 欧元；若购买 1 套含实体芯片的
DevKit（300 欧元）并选择全球经济运输（15 欧元），常规合计约 385 欧元，
不含增值税、进口税或当地清关费。价格与补贴名额可能变化，付款前应重新使用
官方计算器确认。

## 7. GitHub 提交状态

1. `info.yaml` 作者已填写为 `Jackson Haley`。
2. 顶层模块已按 GitHub 账户设置为 `tt_um_lungmen_gov_tt8_cpu`，并已同步
   `info.yaml`、`src/project.v`、`test/tb.v`。
3. 提交 `ef67b0b` 的 GitHub Actions 已取得 RTL test、1x1 GDS、precheck、
   gate-level test 和 viewer 全绿；详细指标见 `docs/verification.md`。
