import json
import random
import hashlib


def generate_mac(i):
    return f"02:11:22:33:{(i // 256):02x}:{(i % 256):02x}"


def generate_shared_info(
    m=64,  # number of total APs in β
    n=16,  # number of TXAPs in A per burst
    L=38,  # number of delay levels
    DS=800,  # delay step (µs)
    BD=102400,  # base delay (µs)
    total_bursts=8,
    seed="chaos-shared-secret",
):
    # Generate β set (m MAC addresses)
    beta = [generate_mac(i) for i in range(m)]

    # Derive alpha sets for each burst
    alpha_sets = []
    for i in range(total_bursts):
        s = int(hashlib.sha256((seed + str(i)).encode()).hexdigest(), 16)
        beta_shuffled = beta[:]
        random.Random(s).shuffle(beta_shuffled)
        alpha = beta_shuffled[:n]
        alpha_sets.append(alpha)

    shared = {
        "beta": beta,
        "n": n,
        "L": L,
        "DS": DS,
        "BD": BD,
        "total_bursts": total_bursts,
        "seed": seed,
        "alpha_sets": alpha_sets,
    }

    with open("./chaos_shared.json", "w") as f:
        json.dump(shared, f, indent=2)


if __name__ == "__main__":
    generate_shared_info()
