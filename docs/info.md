<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

Tiny8 is a compact, host-programmable 8-bit CPU designed for a single Tiny
Tapeout tile. A host writes up to 16 program bytes through `ui_in`, pulses
`START`, and then either runs continuously or clocks one instruction at a
time. The selected R0-R3 register is visible on `uo_out`.

The CPU has four 8-bit registers, a 4-bit program counter, zero and carry
flags, and a one-cycle ALU. Its instruction set includes load, move, input,
add, subtract, bitwise logic, shifts, unconditional and zero-conditional
branches, and halt. LDI is the only two-byte instruction.

The active-low reset is synchronous. It clears all registers, flags, loader
state, and all 16 program bytes. `START` restarts execution without erasing
the loaded program.

## How to test

1. Keep `ena=1`, assert `rst_n=0`, and provide at least one rising clock
   edge. Release reset.
2. Put each program byte on `ui_in[7:0]`, set `uio[0]=1`, and pulse the
   clock once. Bytes load sequentially from address zero.
3. Set `uio[0]=0`, pulse `uio[1]` (`START`) for one rising edge.
4. Hold `uio[3]` high for continuous execution, or pulse `uio[2]` for
   single-step execution.
5. Select R0-R3 with `uio[5:4]`, read its value on `uo[7:0]`, and monitor
   `uio[7]` for HALTED and `uio[6]` for the zero flag.

Example program bytes `10 05 14 03 31 F0` load 5 into R0, load 3 into R1,
add R1 to R0, and halt. The final R0 output is `08`.

## External hardware

A Tiny Tapeout demo board and a microcontroller or FPGA able to drive the
clock, reset, `ui`, and control pins. No external memory is required.

The project requests one 1x1 tile and a 10 MHz clock. These are design targets,
not silicon guarantees; use the repository GDS action and gate-level test for
the selected shuttle before submission.
