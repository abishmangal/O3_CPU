# sim.py -- entry point: load workload, run cycle loop, print traces.

import sys
from lane import decode_lane
from trace import print_cycle
from tables import FUSION_PAIRS

WINDOW_BYTES = 32
LANES = 6


def load_workload(path):
    with open(path) as f:
        return bytes(int(t, 16) for t in f.read().split())


def run(stream, name, verbose=False):
    print(f"\n=== Workload {name} ===")
    tot = {"cycles": 0, "instrs": 0, "bytes": 0,
           "muops": 0, "fusion": 0, "msrom": 0}
    pos, cycle = 0, 0

    while pos < len(stream):
        window = stream[pos:pos + WINDOW_BYTES]
        lanes = []
        stats = {"instrs": 0, "bytes": 0, "muops": 0, "fusion": 0, "msrom": 0}
        off = 0

        for _ in range(LANES):
            if off >= len(window):
                break
            di, new_abs = decode_lane(stream, pos + off)
            new_off = new_abs - pos
            if di.length == 0 or new_off > WINDOW_BYTES:
                break   # instruction straddles the 32-byte window: next cycle
            raw = stream[pos + off:new_abs]

            # Macro-fusion with the immediately preceding lane
            if lanes and not lanes[-1][0].fused and \
               (lanes[-1][0].mnemonic, di.mnemonic) in FUSION_PAIRS:
                di.fused = True
                di.muops = 0            # the pair is one μop, counted on the CMP/TEST
                stats["fusion"] += 1

            stats["muops"] += di.muops
            if di.msrom:
                stats["msrom"] += 1
            lanes.append((di, raw))
            stats["instrs"] += 1
            off = new_off

        stats["bytes"] = off
        print_cycle(cycle, window, lanes, stats, verbose)

        tot["cycles"] += 1
        for k in ("instrs", "bytes", "muops", "fusion", "msrom"):
            tot[k] += stats[k]
        pos += off
        cycle += 1

    print(f"\n--- {name} summary ---")
    print(f"Cycles               : {tot['cycles']}")
    print(f"Total instructions   : {tot['instrs']}")
    print(f"Total bytes          : {tot['bytes']}")
    print(f"Total μops           : {tot['muops']}")
    print(f"Total fusion events  : {tot['fusion']}")
    print(f"Total MSROM events   : {tot['msrom']}")
    if tot["cycles"]:
        c = tot["cycles"]
        print(f"Avg instr/cycle      : {tot['instrs'] / c:.2f}")
        print(f"Avg bytes/cycle      : {tot['bytes'] / c:.2f}")
        print(f"Avg μops/cycle       : {tot['muops'] / c:.2f}")
    print()


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "-v"]
    verbose = "-v" in sys.argv[1:]
    if not args:
        print("usage: python sim.py [-v] workloads/W1.txt [more...]")
        sys.exit(1)
    for path in args:
        run(load_workload(path), path.split("/")[-1].replace(".txt", ""), verbose)
