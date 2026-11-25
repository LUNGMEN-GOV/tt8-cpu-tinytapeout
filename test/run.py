"""Cross-platform Cocotb runner; equivalent to the official Makefile RTL run."""

from pathlib import Path

from cocotb_tools.runner import get_runner


HERE = Path(__file__).resolve().parent
SOURCES = [
    HERE.parent / "src" / "project.v",
    HERE.parent / "src" / "tiny8_cpu.v",
    HERE / "tb.v",
]


def main():
    runner = get_runner("icarus")
    runner.build(
        sources=SOURCES,
        hdl_toplevel="tb",
        build_dir=HERE / "sim_build" / "rtl",
        always=True,
        waves=False,
    )
    runner.test(
        hdl_toplevel="tb",
        test_module="test",
        build_dir=HERE / "sim_build" / "rtl",
        waves=False,
    )


if __name__ == "__main__":
    main()
