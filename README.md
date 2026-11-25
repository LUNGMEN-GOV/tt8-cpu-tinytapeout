![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/test/badge.svg) ![](../../workflows/fpga/badge.svg)

# Tiny8 CPU：Tiny Tapeout 单 Tile 8 位处理器

这是一个以低流片成本为首要约束的 8 位微型 CPU，基于 Tiny Tapeout
官方 SKY130 Verilog 模板。项目配置请求 **1x1 Tile**，包含完整 RTL、
Cocotb 自检、汇编器、示例程序和使用文档。

主要规格：

- 8 位数据通路，4 个通用寄存器 R0-R3；
- 8 字节可装载程序存储器，3 位程序计数器；
- ADD、SUB、AND、OR、XOR、NOT、SHL、SHR；
- JMP、JZ、JNZ、LDI、MOV、IN、NOP、HALT；
- 连续运行和单步执行；
- 低有效同步复位，复位清除程序与全部状态；
- 目标时钟 10 MHz，最终频率和面积以官方 GDS workflow 报告为准。

详细资料见 [docs/USAGE_zh.md](docs/USAGE_zh.md)，测试说明见
[test/README.md](test/README.md)，验证结论见
[docs/verification.md](docs/verification.md)。

作者信息已填写为 Jackson Haley；顶层模块已加入 GitHub 用户名，设置为
`tt_um_lungmen_gov_tt8_cpu`。

快速验证：

```sh
cd test
python -m pip install -r requirements.txt
make -B
```

汇编示例：

```sh
python tools/assembler.py examples/demo.asm -o examples/demo.hex
python -m unittest tools.test_assembler -v
```

以下保留上游模板原始说明。

- [Read the documentation for project](docs/info.md)

## What is Tiny Tapeout?

Tiny Tapeout is an educational project that aims to make it easier and cheaper than ever to get your digital and analog designs manufactured on a real chip.

To learn more and get started, visit https://tinytapeout.com.

## Set up your Verilog project

1. Add your Verilog files to the `src` folder.
2. Edit the [info.yaml](info.yaml) and update information about your project, paying special attention to the `source_files` and `top_module` properties. If you are upgrading an existing Tiny Tapeout project, check out our [online info.yaml migration tool](https://tinytapeout.github.io/tt-yaml-upgrade-tool/).
3. Edit [docs/info.md](docs/info.md) and add a description of your project.
4. Adapt the testbench to your design. See [test/README.md](test/README.md) for more information.

The GitHub action will automatically build the ASIC files using [LibreLane](https://www.zerotoasiccourse.com/terminology/librelane/).

## Enable GitHub actions to build the results page

- [Enabling GitHub Pages](https://tinytapeout.com/faq/#my-github-action-is-failing-on-the-pages-part)

## Resources

- [FAQ](https://tinytapeout.com/faq/)
- [Digital design lessons](https://tinytapeout.com/digital_design/)
- [Learn how semiconductors work](https://tinytapeout.com/siliwiz/)
- [Join the community](https://tinytapeout.com/discord)
- [Build your design locally](https://www.tinytapeout.com/guides/local-hardening/)

## What next?

- [Submit your design to the next shuttle](https://app.tinytapeout.com/).
- Edit [this README](README.md) and explain your design, how it works, and how to test it.
- Share your project on your social network of choice:
  - LinkedIn [#tinytapeout](https://www.linkedin.com/search/results/content/?keywords=%23tinytapeout) [@TinyTapeout](https://www.linkedin.com/company/100708654/)
  - Mastodon [#tinytapeout](https://chaos.social/tags/tinytapeout) [@matthewvenn](https://chaos.social/@matthewvenn)
  - X (formerly Twitter) [#tinytapeout](https://twitter.com/hashtag/tinytapeout) [@tinytapeout](https://twitter.com/tinytapeout)
  - Bluesky [@tinytapeout.com](https://bsky.app/profile/tinytapeout.com)
