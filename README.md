# CHAOS_FINAL

The final project for the wireless connection course.

## 📁 Files Overview

- `GEN_SHARED_INFO.py`: Generates the shared configuration (`chaos_shared.json`) including the MAC address set `β`, derived permutation subsets `α`, and transmission parameters.
- `CHAOS_sender.py`: Encodes and sends a binary message over multiple beacon bursts by manipulating TSF delays and AP permutations.
- `CHAOS_receiver.py`: Receives the beacon bursts from a `.pcap` file, decodes the permutations and delays, and reconstructs the original message.

---

## 🔧 Requirements

Install dependencies via pip:

```bash
pip install -r requirements.txt
```

```
## 🚀 Usage

This covert communication system consists of three components: a shared configuration generator, a receiver, and a sender. **You must execute them in the following order**:

### 1. Generate Shared Parameters

The sender and receiver must agree on a shared configuration file (`chaos_shared.json`), which contains the address pool (`β`), selected subsets (`α`), and timing parameters.

Run:

```bash
python GEN_SHARED_INFO.py
```

This will generate `chaos_shared.json` in the current directory.

---

### 2. Start the Receiver First

The receiver waits for incoming bursts (beacon frames) and decodes them as they arrive.

Run:

```bash
sudo python CHAOS_receiver.py
```

> ℹ️ The receiver will wait and try to decode each burst as it arrives.  
> It will continue running until all expected bursts are received (default is 8).  
> **Packet loss is expected** due to the nature of Wi-Fi broadcasts — the system is designed to tolerate missing bursts.

---

### 3. Send the Message via Beacon Bursts

Edit the message inside `CHAOS_sender.py`:

```python
msg = "Your secret message here"
```

Then run:

```bash
sudo python CHAOS_sender.py
```

The sender will encode the message into bursts of Wi-Fi beacon frames using permutations and TSF timing manipulations. These bursts are sent in sequence, and the receiver captures them in real-time.

---

### 🧪 Simulation

The sender saves the beacon bursts into `burst.pcap`, which the receiver will repeatedly attempt to read and decode. You can emulate message sending without actual Wi-Fi injection.
I do not have any device viable to send custom beacon frames, so I cannot ensure the functionality of the system in the real-world scenario.

## 🎥 Demo

A demonstration of the CHAOS covert channel in action is available in the video below:

[▶️ Watch CHAOS_DEMO.mkv](./CHAOS_DEMO.mkv)
