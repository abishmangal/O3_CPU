# tables.py -- all ISA data lives here.

# opcode -> (mnemonic, has_modrm, pattern)
#   RM   = ModRM, reg is source, r/m is destination (store form if mem)
#   MR   = ModRM, reg is destination, r/m is source (load form if mem)
#   MI   = ModRM + imm8
#   REL8 = 1-byte relative displacement
OPCODES = {
    0x01: ("ADD",  True,  "RM"),
    0x29: ("SUB",  True,  "RM"),
    0x31: ("XOR",  True,  "RM"),
    0x39: ("CMP",  True,  "RM"),
    0x85: ("TEST", True,  "RM"),
    0x89: ("MOV",  True,  "RM"),
    0x8B: ("MOV",  True,  "MR"),
    0x83: ("GRP1", True,  "MI"),
    0x75: ("JNE",  False, "REL8"),
    0x74: ("JE",   False, "REL8"),
}

GRP1_SUB = {0: "ADD", 1: "OR", 2: "ADC", 3: "SBB",
            4: "AND", 5: "SUB", 6: "XOR", 7: "CMP"}

PREFIXES = {0x66, 0x67, 0xF0, 0xF2, 0xF3,
            0x2E, 0x36, 0x3E, 0x26, 0x64, 0x65}
REX = set(range(0x40, 0x50))

# mnemonic -> (muop_count, is_msrom)
MUOP_RULES = {
    "ADD": (1, False), "SUB": (1, False), "XOR": (1, False),
    "CMP": (1, False), "TEST": (1, False), "MOV": (1, False),
    "JNE": (1, False), "JE": (1, False), "OR": (1, False),
    "AND": (1, False), "ADC": (1, False), "SBB": (1, False),
    "CPUID": (30, True),
}

FUSION_PAIRS = {("CMP", "JNE"), ("CMP", "JE"),
                ("TEST", "JNE"), ("TEST", "JE")}
