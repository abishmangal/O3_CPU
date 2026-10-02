# trace.py -- per-cycle trace formatting.

def _fmt_hex(raw):
    return " ".join(f"{x:02X}" for x in raw)


def _fmt_fields(di):
    parts = []
    if di.prefixes:
        parts.append("pfx=" + ",".join(f"{p:02X}" for p in di.prefixes))
    if di.rex:
        parts.append(f"rex={di.rex:02X}")
    o = di.operands
    if "mod" in o:
        parts.append(f"modrm(mod={o['mod']} reg={o['reg']} rm={o['rm']})")
    if "sib" in o:
        s = o["sib"]
        parts.append(f"sib(s={s['scale']} i={s['index']} b={s['base']})")
    for k in ("disp", "imm", "rel"):
        if k in o:
            parts.append(f"{k}={o[k]:#x}")
    return " ".join(parts) or "-"


def print_cycle(cycle, window, lanes, stats, verbose=False):
    print(f"Cycle {cycle}")
    print("-" * 56)
    print(f"Bytes available : {len(window)}")

    for n in range(6):
        if n < len(lanes):
            di, raw = lanes[n]
            tail = "fused" if di.fused else f"{di.muops} μop" + ("s" if di.muops != 1 else "")
            if di.msrom:
                tail += " [MSROM]"
            print(f"D{n} : {_fmt_hex(raw):<24} {di.mnemonic:<5} "
                  f"{di.cls:<6} {di.length}B → {tail}")
            if verbose:
                print(f"      fields: {_fmt_fields(di)}")
        else:
            print(f"D{n} : idle")

    print(f"Instructions decoded : {stats['instrs']}")
    print(f"Bytes consumed       : {stats['bytes']}")
    print(f"μops generated       : {stats['muops']}")
    print(f"Fusion events        : {stats['fusion']}")
    print(f"MSROM events         : {stats['msrom']}")
    print("-" * 56)
