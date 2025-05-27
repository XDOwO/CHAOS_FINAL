import json
import struct
import time
import random
import os
from math import factorial, floor, log2
from scapy.all import RadioTap, Dot11, Dot11Beacon, sendp, Raw, wrpcap
from scapy.layers.dot11 import Dot11Elt


# --- Load shared config ---
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
IFACE = "wlp85s0f0mon"  # Your monitor interface

T = factorial(N) * (L**N)
BITS_PER_BURST = floor(log2(T))


# --- Permutation helpers ---
def nth_permutation(alpha, index):
    lst = list(alpha)
    result = []
    for _ in range(len(lst)):
        f = factorial(len(lst) - 1)
        pos = index // f
        result.append(lst.pop(pos))
        index %= f
    return result


def baseL_digits(x, base, length):
    return [(x // (base**i)) % base for i in range(length)]


# --- Craft beacon with custom TSF ---
def make_beacon(mac, ssid, tsf):
    dot11 = Dot11(type=0, subtype=8, addr1="ff:ff:ff:ff:ff:ff", addr2=mac, addr3=mac)
    beacon = Dot11Beacon(cap="ESS")
    essid = Dot11Elt(ID="SSID", info=ssid)
    frame = RadioTap() / dot11 / beacon / essid
    raw_bytes = bytearray(bytes(frame))
    tsf_bytes = struct.pack("<Q", tsf)
    raw_bytes[8:16] = tsf_bytes
    return bytes(raw_bytes)  # return bytes, not Raw or Packet


# --- Main transmission function ---
def chaos_send_message(message_bits):
    if len(message_bits) <= TOTAL_BURSTS * BITS_PER_BURST:
        pad = TOTAL_BURSTS * BITS_PER_BURST - len(message_bits)
        message_bits += "0" * pad
        print("Length of message", len(message_bits))
        print("bitstring", message_bits)

    else:
        print("Message too long.")
        return
    tbtt_base = (int(time.time() * 1e6) // BD) * BD
    print(f"[+] TSF base set to {tbtt_base}")
    while True:
        for burst_index in range(TOTAL_BURSTS):
            bit_chunk = message_bits[
                burst_index * BITS_PER_BURST : (burst_index + 1) * BITS_PER_BURST
            ]
            print(f"Sending busrt #{burst_index}: {bit_chunk}")
            message_index = int(bit_chunk, 2)

            perm_index = message_index // (L**N)
            delay_index = message_index % (L**N)

            alpha = ALPHAS[burst_index % TOTAL_BURSTS]
            permutation = nth_permutation(alpha, perm_index)
            delays = baseL_digits(delay_index, L, N)

            # print("idxidxidx", perm_index, delay_index, delays)
            # print(permutation)
            pkts = []
            shuffled_beta = list(BETA)
            random.shuffle(shuffled_beta)
            idx = 0
            for i, v in enumerate(shuffled_beta):
                if v in permutation:
                    shuffled_beta[i] = permutation[idx]
                    idx += 1
            for mac in shuffled_beta:
                if mac in permutation:
                    i = permutation.index(mac)
                    epsilon = random.randint(0, DS // 2)
                    tsf = tbtt_base + delays[i] * DS + epsilon
                else:
                    tsf = int(time.time() * 1e6)
                pkt = make_beacon(mac, "CHAOS", tsf)
                # sendp(pkt, iface=IFACE, verbose=0)
                pkt = RadioTap(pkt)
                pkts.append(pkt)
                # print(
                #     f"  → Beacon from {mac} | TSF={tsf} | {'TXAP' if mac in permutation else 'CAP'} | {burst_index}"
                # )
            wrpcap("burst.pcap", pkts)
            print(f"tbtt-base:{tbtt_base}")
            print(f"[=] Permutation index:{perm_index}, Delay index: {delay_index}")
            print(f"Permutation:{[ i[-2:] for i in permutation ]}")
            print(f"Burst index {burst_index} transmitted.")
            tbtt_base += BD  # gap before next burst
            while tbtt_base > int(time.time() * 1e6):
                time.sleep(0.01)
                pass


# --- Example usage ---
if __name__ == "__main__":
    msg = "Peumonoultramicroscopicsiliconvolcanoconiosis"
    bitstring = "".join(f"{ord(c):08b}" for c in msg)
    print("bitstring", bitstring)
    print("BITS_PER_BURST:", BITS_PER_BURST)
    chaos_send_message(bitstring)
