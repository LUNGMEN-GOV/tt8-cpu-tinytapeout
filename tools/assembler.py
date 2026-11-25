#!/usr/bin/env python3
"""Two-pass assembler for the Tiny8 16-byte instruction set."""

import argparse
import pathlib
import re
import sys


OPCODES = {
    "NOP": 0x0,
    "LDI": 0x1,
    "MOV": 0x2,
    "ADD": 0x3,
    "SUB": 0x4,
    "AND": 0x5,
    "OR": 0x6,
    "XOR": 0x7,
    "NOT": 0x8,
    "SHL": 0x9,
    "SHR": 0xA,
    "JMP": 0xB,
    "JZ": 0xC,
    "JNZ": 0xD,
    "IN": 0xE,
    "HALT": 0xF,
}


def parse_number(text, labels):
    key = text.upper()
    if key in labels:
        return labels[key]
    return int(text, 0)


def parse_register(text, line_no):
    match = re.fullmatch(r"R([0-3])", text.upper())
    if not match:
        raise ValueError(f"line {line_no}: expected R0..R3, got {text!r}")
    return int(match.group(1))


def source_lines(text):
    result = []
    for line_no, raw in enumerate(text.splitlines(), 1):
        code = raw.split(";", 1)[0].strip()
        if code:
            result.append([line_no, code])
    return result


def split_label(line):
    if ":" not in line:
        return None, line
    label, instruction = line.split(":", 1)
    label = label.strip().upper()
    if not re.fullmatch(r"[A-Z_][A-Z0-9_]*", label):
        raise ValueError(f"invalid label {label!r}")
    return label, instruction.strip()


def instruction_size(text):
    mnemonic = re.split(r"[\s,]+", text.strip())[0].upper()
    if mnemonic not in OPCODES:
        raise ValueError(f"unknown instruction {mnemonic!r}")
    return 2 if mnemonic == "LDI" else 1


def assemble(text):
    lines = source_lines(text)
    labels = {}
    address = 0

    for line_no, code in lines:
        label, instruction = split_label(code)
        if label:
            if label in labels:
                raise ValueError(f"line {line_no}: duplicate label {label}")
            labels[label] = address
        if instruction:
            address += instruction_size(instruction)
        if address > 16:
            raise ValueError(f"line {line_no}: program exceeds 16 bytes")

    image = []
    for line_no, code in lines:
        _, instruction = split_label(code)
        if not instruction:
            continue
        fields = [part for part in re.split(r"[\s,]+", instruction) if part]
        mnemonic = fields[0].upper()
        opcode = OPCODES[mnemonic] << 4

        if mnemonic in {"NOP", "HALT"}:
            if len(fields) != 1:
                raise ValueError(f"line {line_no}: {mnemonic} takes no operands")
            image.append(opcode)
        elif mnemonic == "LDI":
            if len(fields) != 3:
                raise ValueError(f"line {line_no}: LDI requires Rd, immediate")
            rd = parse_register(fields[1], line_no)
            value = parse_number(fields[2], labels)
            if not 0 <= value <= 0xFF:
                raise ValueError(f"line {line_no}: immediate does not fit 8 bits")
            image.extend([opcode | (rd << 2), value])
        elif mnemonic in {"MOV", "ADD", "SUB", "AND", "OR", "XOR"}:
            if len(fields) != 3:
                raise ValueError(f"line {line_no}: {mnemonic} requires Rd, Rs")
            rd = parse_register(fields[1], line_no)
            rs = parse_register(fields[2], line_no)
            image.append(opcode | (rd << 2) | rs)
        elif mnemonic in {"NOT", "SHL", "SHR", "IN"}:
            if len(fields) != 2:
                raise ValueError(f"line {line_no}: {mnemonic} requires Rd")
            rd = parse_register(fields[1], line_no)
            image.append(opcode | (rd << 2))
        else:
            if len(fields) != 2:
                raise ValueError(f"line {line_no}: {mnemonic} requires address")
            target = parse_number(fields[1], labels)
            if not 0 <= target <= 0xF:
                raise ValueError(f"line {line_no}: branch address does not fit 4 bits")
            image.append(opcode | target)

    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=pathlib.Path)
    parser.add_argument("-o", "--output", type=pathlib.Path)
    parser.add_argument("--pad", action="store_true", help="pad image to 16 bytes")
    args = parser.parse_args()

    try:
        image = assemble(args.source.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        parser.error(str(error))

    if args.pad:
        image += [0] * (16 - len(image))
    output = "\n".join(f"{byte:02X}" for byte in image) + "\n"
    if args.output:
        args.output.write_text(output, encoding="ascii")
    else:
        sys.stdout.write(output)


if __name__ == "__main__":
    main()
