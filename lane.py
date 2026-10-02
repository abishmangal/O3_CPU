# lane.py -- the six decode steps plus decode_lane().

from dataclasses import dataclass, field
from tables import OPCODES, GRP1_SUB, PREFIXES, REX, MUOP_RULES


@dataclass
class DecodedInstr:
    mnemonic: str
    length: int
    cls: str
    muops: int
    msrom: bool
    fused: bool = False
    rex: int = 0
    prefixes: list = field(default_factory=list)
    operands: dict = field(default_factory=dict)


# Step 2: prefixes
def step_prefixes(b, i):
    rex, flags = 0, []
    while i < len(b) and (b[i] in PREFIXES or b[i] in REX):
        if b[i] in REX:
            rex = b[i]
        else:
            flags.append(b[i])
        i += 1
    return rex, flags, i


# Step 3: opcode -> (mnemonic, has_modrm, pattern, new_i)
def step_opcode(b, i):
    if i >= len(b):
        return "UNKNOWN", False, "", i
    op = b[i]; i += 1
    if op == 0x0F and i < len(b):
        op2 = b[i]; i += 1
        if op2 == 0xA2:
            return "CPUID", False, "", i
        return "UNKNOWN", False, "", i
    entry = OPCODES.get(op)
    if not entry:
        return "UNKNOWN", False, "", i
    mnem, has_modrm, pattern = entry
    return mnem, has_modrm, pattern, i


# Step 4: ModRM / SIB / displacement / immediate
def step_operands(b, i, has_modrm, pattern):
    ops = {}
    if has_modrm and i < len(b):
        modrm = b[i]; i += 1
        mod, reg, rm = modrm >> 6, (modrm >> 3) & 7, modrm & 7
        ops.update(mod=mod, reg=reg, rm=rm)

        sib_base5 = False
        if mod != 3 and rm == 4 and i < len(b):
            sib = b[i]; i += 1
            ops["sib"] = {"scale": sib >> 6,
                          "index": (sib >> 3) & 7,
                          "base": sib & 7}
            sib_base5 = (sib & 7) == 5

        if mod == 1:
            ops["disp"] = int.from_bytes(b[i:i+1], "little"); i += 1
        elif mod == 2 or (mod == 0 and (rm == 5 or sib_base5)):
            ops["disp"] = int.from_bytes(b[i:i+4], "little"); i += 4

    if pattern == "MI":
        ops["imm"] = int.from_bytes(b[i:i+1], "little"); i += 1
    elif pattern == "REL8":
        ops["rel"] = int.from_bytes(b[i:i+1], "little"); i += 1
    return ops, i


# Step 5: classify
def step_classify(mnemonic, pattern, ops):
    if mnemonic in ("ADD", "SUB", "XOR", "CMP", "TEST",
                    "OR", "AND", "ADC", "SBB"):
        return "ALU"
    if mnemonic == "MOV":
        if ops.get("mod", 3) == 3:
            return "MOV"
        return "LOAD" if pattern == "MR" else "STORE"
    if mnemonic in ("JNE", "JE"):
        return "BRANCH"
    if mnemonic == "CPUID":
        return "MSROM"
    return "OTHER"


# Step 6: μops
def step_muops(mnemonic):
    return MUOP_RULES.get(mnemonic, (1, False))


# Step 1 (length) falls out of the offsets after steps 2-4.
def decode_lane(b, i):
    """Decode one instruction at offset i. Returns (DecodedInstr, new_i)."""
    start = i
    rex, flags, i = step_prefixes(b, i)
    mnem, has_modrm, pattern, i = step_opcode(b, i)
    ops, i = step_operands(b, i, has_modrm, pattern)
    if mnem == "GRP1":
        mnem = GRP1_SUB.get(ops.get("reg", 0), "GRP1")
    cls = step_classify(mnem, pattern, ops)
    muops, msrom = step_muops(mnem)
    i = min(i, len(b))
    return DecodedInstr(mnemonic=mnem, length=i - start, cls=cls,
                        muops=muops, msrom=msrom, rex=rex,
                        prefixes=flags, operands=ops), i
