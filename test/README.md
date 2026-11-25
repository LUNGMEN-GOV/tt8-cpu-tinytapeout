# Tiny8 CPU 仿真测试

本目录沿用官方模板的 Cocotb/Icarus 流程。四个自检用例覆盖同步复位、
顺序装载、全部 ALU 指令、三类跳转、IN/MOV、单步、`ena` 暂停、
START 重启，以及复位擦除程序与状态。

## Setting up

安装 Icarus Verilog 和 Python，然后执行：

## How to run

To run the RTL simulation:

```sh
python -m pip install -r requirements.txt
make -B
```

Windows 下也可以不用 `make`，直接使用 Cocotb runner：

```powershell
python run.py
```

To run gatelevel simulation, first harden your project and copy `../runs/wokwi/results/final/verilog/gl/{your_module_name}.v` to `gate_level_netlist.v`.

Then run:

```sh
make -B GATES=yes
```

If you wish to save the waveform in VCD format instead of FST format, edit tb.v to use `$dumpfile("tb.vcd");` and then run:

```sh
make -B FST=
```

This will generate `tb.vcd` instead of `tb.fst`.

## How to view the waveform file

Using GTKWave

```sh
gtkwave tb.fst tb.gtkw
```

Using Surfer

```sh
surfer tb.fst
```
