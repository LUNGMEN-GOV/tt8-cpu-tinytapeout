import pathlib
import sys
import unittest

TOOLS_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_DIR = TOOLS_DIR.parent
sys.path.insert(0, str(TOOLS_DIR))

from assembler import assemble


class AssemblerTests(unittest.TestCase):
    def test_demo(self):
        text = (PROJECT_DIR / "examples" / "demo.asm").read_text(encoding="utf-8")
        self.assertEqual(assemble(text), [0x10, 0x05, 0x14, 0x03, 0x31, 0xF0])

    def test_labels_and_all_formats(self):
        image = assemble(
            """
            start: LDI R2, 0xff
                   MOV R1, R2
                   NOT R1
                   IN R3
                   JZ done
                   JMP start
            done:  HALT
            """
        )
        self.assertEqual(image, [0x18, 0xFF, 0x26, 0x84, 0xEC, 0xC7, 0xB0, 0xF0])

    def test_rejects_oversize_program(self):
        with self.assertRaisesRegex(ValueError, "exceeds 16 bytes"):
            assemble("\n".join(["NOP"] * 17))


if __name__ == "__main__":
    unittest.main()
