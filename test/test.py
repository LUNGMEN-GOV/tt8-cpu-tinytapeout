# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, Timer


def controls(*, load=0, start=0, step=0, run=0, reg=0):
    return load | (start << 1) | (step << 2) | (run << 3) | ((reg & 3) << 4)


async def initialise(dut):
    cocotb.start_soon(Clock(dut.clk, 100, unit="ns").start())  # 10 MHz
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 3)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def load_program(dut, program):
    assert len(program) <= 16
    for byte in program:
        dut.ui_in.value = byte
        dut.uio_in.value = controls(load=1)
        await RisingEdge(dut.clk)
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    await RisingEdge(dut.clk)


async def start_cpu(dut, *, run=True):
    dut.uio_in.value = controls(start=1)
    await RisingEdge(dut.clk)
    dut.uio_in.value = controls(run=int(run))


async def run_until_halt(dut, limit=64):
    for _ in range(limit):
        await RisingEdge(dut.clk)
        if int(dut.uio_out.value) & 0x80:
            return
    raise AssertionError("CPU did not halt before cycle limit")


async def read_register(dut, index):
    dut.uio_in.value = controls(reg=index)
    await Timer(1, unit="ns")
    return int(dut.uo_out.value)


@cocotb.test()
async def test_reset_loader_and_arithmetic_logic(dut):
    await initialise(dut)
    assert int(dut.uo_out.value) == 0
    assert int(dut.uio_out.value) == 0x80
    assert int(dut.uio_oe.value) == 0xC0

    program = [
        0x10, 0x12,  # LDI R0, 0x12
        0x14, 0x05,  # LDI R1, 0x05
        0x31,        # ADD R0, R1 -> 0x17
        0x41,        # SUB R0, R1 -> 0x12
        0x51,        # AND R0, R1 -> 0x00
        0x61,        # OR  R0, R1 -> 0x05
        0x71,        # XOR R0, R1 -> 0x00
        0x80,        # NOT R0     -> 0xFF
        0x90,        # SHL R0     -> 0xFE
        0xA0,        # SHR R0     -> 0x7F
        0xF0,        # HALT
    ]
    await load_program(dut, program)
    await start_cpu(dut)
    await run_until_halt(dut)

    assert await read_register(dut, 0) == 0x7F
    assert await read_register(dut, 1) == 0x05
    assert int(dut.uio_out.value) & 0xC0 == 0x80


@cocotb.test()
async def test_jumps_and_flags(dut):
    await initialise(dut)
    program = [
        0x10, 0x00,  # 0: LDI R0, 0 -> Z=1
        0xC5,        # 2: JZ 5 (taken)
        0x10, 0xEE,  # 3: skipped
        0x14, 0x03,  # 5: LDI R1, 3
        0x45,        # 7: SUB R1, R1 -> 0, Z=1
        0xDB,        # 8: JNZ 11 (not taken)
        0xBC,        # 9: JMP 12
        0xF0, 0x00,  # 10..11: skipped/padding
        0x18, 0x5A,  # 12: LDI R2, 0x5A -> Z=0
        0xDF,        # 14: JNZ 15 (taken)
        0xF0,        # 15: HALT
    ]
    await load_program(dut, program)
    await start_cpu(dut)
    await run_until_halt(dut)

    assert await read_register(dut, 0) == 0x00
    assert await read_register(dut, 1) == 0x00
    assert await read_register(dut, 2) == 0x5A
    assert int(dut.uio_out.value) & 0x40 == 0


@cocotb.test()
async def test_input_move_step_and_enable(dut):
    await initialise(dut)
    await load_program(dut, [0xEC, 0x23, 0xF0])  # IN R3; MOV R0,R3; HALT
    await start_cpu(dut, run=False)

    dut.ui_in.value = 0xA6
    dut.uio_in.value = controls(step=1, reg=3)
    await RisingEdge(dut.clk)
    dut.uio_in.value = controls(reg=3)
    await RisingEdge(dut.clk)
    assert int(dut.uo_out.value) == 0xA6

    dut.uio_in.value = controls(step=1, reg=0)
    await RisingEdge(dut.clk)
    dut.uio_in.value = controls(reg=0)
    await RisingEdge(dut.clk)
    assert int(dut.uo_out.value) == 0xA6

    dut.ena.value = 0
    dut.uio_in.value = controls(step=1)
    await RisingEdge(dut.clk)
    assert int(dut.uo_out.value) == 0
    assert int(dut.uio_out.value) == 0
    assert int(dut.uio_oe.value) == 0

    dut.ena.value = 1
    dut.uio_in.value = controls(step=1)
    await RisingEdge(dut.clk)
    dut.uio_in.value = controls(reg=0)
    await RisingEdge(dut.clk)
    assert int(dut.uio_out.value) & 0x80
    assert int(dut.uo_out.value) == 0xA6


@cocotb.test()
async def test_restart_preserves_program_and_reset_erases_it(dut):
    await initialise(dut)
    await load_program(dut, [0x10, 0x2A, 0xF0])
    await start_cpu(dut)
    await run_until_halt(dut)
    assert await read_register(dut, 0) == 0x2A

    await start_cpu(dut)
    await run_until_halt(dut)
    assert await read_register(dut, 0) == 0x2A

    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    dut.uio_in.value = controls(reg=0)
    await RisingEdge(dut.clk)
    assert int(dut.uo_out.value) == 0
    assert int(dut.uio_out.value) & 0x80
