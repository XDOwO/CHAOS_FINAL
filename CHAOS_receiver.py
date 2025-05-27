import json
import time
import struct
import itertools
import os
from math import factorial, log2, floor
from scapy.all import rdpcap, Dot11

# Load shared config
with open("chaos_shared.json") as f:
    config = json.load(f)

BETA = config["beta"]
N = config["n"]
L = config["L"]
DS = config["DS"]
BD = config["BD"]
TOTAL_BURSTS = config["total_bursts"]
SEED = config["seed"]
ALPHAS = config["alpha_sets"]
IFACE = "wlp85s0f0mon"

T = factorial(N) * (L**N)
BITS_PER_BURST = floor(log2(T))


def tsf_from_pkt(pkt):
    raw_bytes = bytes(pkt)
    return struct.unpack("<Q", raw_bytes[8:16])[0]


def decode_delay_levels(tsfs, base_tsf):
    return [floor((tsf - base_tsf) / DS) for tsf in tsfs]


def permutation_index(alpha, perm):
    n = len(perm)
    alpha_index = {val: i for i, val in enumerate(alpha)}

    mapped = [alpha_index[x] for x in perm]

    used = [False] * n
    rank = 0

    for i in range(n):
        count = sum(1 for j in range(mapped[i]) if not used[j])
        rank += count * factorial(n - i - 1)
        used[mapped[i]] = True

    return rank


def capture_burst(pcap_path, poll_interval=0.001):
    seen = {}
    seen_burst_index = set()
    tsf = None
    tsf_base = None
    print("[*] Receiver started. Waiting for bursts...")

    while len(seen) < TOTAL_BURSTS:
        try:
            pkts = rdpcap("burst.pcap")
        except Exception as e:
            # print(f"[!] Failed to read pcap: {e}")
            time.sleep(poll_interval)
            continue

        for pkt in pkts:
            if pkt.haslayer(Dot11) and pkt[Dot11].addr2 in BETA:
                tsf = tsf_from_pkt(pkt)
                if tsf_base is None:
                    tsf_base = (tsf // BD) * BD
                    print(f"[+] TSF base set to {tsf_base}")
                    break
        # Extract all valid MACs in BETA from the capture
        if tsf_base is None or tsf is None:
            continue
        burst_index = floor((tsf - tsf_base) / (BD)) % TOTAL_BURSTS
        alpha = ALPHAS[burst_index]

        txaps = [p for p in pkts if p.haslayer(Dot11) and p[Dot11].addr2 in alpha]
        if len(txaps) < N:
            # print(
            #     f"[~] Only {len(txaps)} in burst.Not enough packets in burst. Waiting..."
            # )
            time.sleep(poll_interval)
            continue

        # Map MAC to TSF
        # tsf_map = {p[Dot11].addr2: tsf_from_pkt(p) for p in txaps}
        tsf_map = [(p[Dot11].addr2, tsf_from_pkt(p)) for p in txaps]
        tbtt_base = (tsf // BD) * BD
        tsf = None
        # Estimate burst index based on time offset
        if burst_index in seen_burst_index:
            # print(f"[~] Duplicate burst #{burst_index}. Skipping...")
            time.sleep(poll_interval)
            continue

        # ordered = sorted([(mac, tsf_map[mac]) for mac in alpha], key=lambda x: x[1])
        perm = [mac for mac, _ in tsf_map]
        tsfs = [tsf for _, tsf in tsf_map]
        delays = decode_delay_levels(tsfs, tbtt_base)
        perm_idx = permutation_index(alpha, perm)
        delay_idx = sum([delays[j] * (L**j) for j in range(N)])
        # print("idxidxidx", perm_idx, delay_idx, delays)
        msg_index = perm_idx * (L**N) + delay_idx
        bits = f"{msg_index:0{BITS_PER_BURST}b}"
        seen[burst_index] = bits
        seen_burst_index.add(burst_index)

        print(f"tbtt-base:{tbtt_base}")
        print(f"[=] Permutation index:{perm_idx}, Delay index: {delay_idx}")
        print(f"Permutation:{[ i[-2:] for i in perm ]}")
        print(f"[✓] Decoded burst #{burst_index}: {bits}")
        print(f"[=] {len(seen)}/{TOTAL_BURSTS} bursts collected.")
        print(f"[=] {seen.keys()} has been collected.")

    # Reassemble message
    full_bits = "".join(seen[i] for i in sorted(seen))
    chars = [chr(int(full_bits[i : i + 8], 2)) for i in range(0, len(full_bits), 8)]
    message = "".join(chars)
    print("\n[✓] Final decoded message:")
    print(message)


# Run the receiver
if __name__ == "__main__":
    if os.path.exists("./burst.pcap"):
        os.remove("./burst.pcap")
    capture_burst("./burst.pcap")
