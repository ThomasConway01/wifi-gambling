# 🎲 Wi-Fi Time Roulette (The Bandwidth Casino)

<p align="center">
  <img src="https://raw.githubusercontent.com/ThomasConway01/wifi-gambling/master/static/assets/banner.png" alt="Wi-Fi Time Roulette" width="100%" onerror="this.style.display='none'"/>
</p>

<p align="center">
  <b>High-Stakes Screen Time: Where Screen Time Meets Authentic European Roulette.</b><br>
  <i>Gamble your device's monthly internet hours on Red, Black, or Straight Up Numbers.<br>
  Double your hours... or lose everything and suffer digital darkness (Wi-Fi disconnection) until the monthly reset!</i>
</p>

<p align="center">
  <a href="https://github.com/ThomasConway01/wifi-gambling/blob/master/LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="License: MIT"/></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python"/></a>
  <a href="https://ui.com/"><img src="https://img.shields.io/badge/Hardware-UniFi%20%7C%20Firewall%20%7C%20Webhook-crimson.svg?style=for-the-badge&logo=ubiquiti&logoColor=white" alt="Routers"/></a>
  <a href="#-mathematical-odds--payout-table"><img src="https://img.shields.io/badge/Casino%20Odds-2.70%25%20Single%20Zero-goldenrod.svg?style=for-the-badge" alt="Single Zero"/></a>
</p>

---

## 💡 The Concept

Why manage screen time with boring parental timers and screen restrictions when you can turn your home or dorm Wi-Fi into an authentic high-stakes casino floor?

- **The Bank:** Every device detected on your Wi-Fi network (iPhones, Androids, gaming PCs, smart TVs, tablets) starts with a monthly allowance of screen time (default: **168 hours / 7 days**).
- **The Wager:** Need more time to binge Netflix or play games? Select your device, pick your physical time tokens (**15m**, **1h**, **6h**, **24h**, or nuclear **ALL-IN**), and place your bet on the felt.
- **The Spin:** Watch the physics-simulated single-zero roulette wheel spin with authentic ceramic ball deceleration, pocket hopping, and real-time synthesized procedural audio.
- **The Consequence:**
  - 🟢 **WIN:** Your hours are credited immediately to your device's network bank.
  - 🔴 **BUST (0h Remaining):** If you run out of time, your device status becomes **`LOCKED OUT`** and the active Network Enforcement Engine (UniFi controller, Windows Firewall, or custom Webhook) **instantly severs your device's Wi-Fi connection** until the next monthly reset!

---

## 🌟 Features

```
  ┌──────────────────┐     ARP & Hostname Sync     ┌──────────────────────┐
  │  Local Wi-Fi LAN  │ ─────────────────────────► │ Network Radar Scanner│
  └──────────────────┘                             └──────────┬───────────┘
           │                                                  │
           │ (Active STAs)                                    ▼
           │                                       ┌──────────────────────┐
           │                                       │ Device Bank (SQLite) │
           │                                       └──────────┬───────────┘
           │                                                  │
           │                                                  ▼
  ┌────────▼─────────┐    Real-time Cutoff Action  ┌──────────────────────┐
  │ UniFi AP / Router│ ◄────────────────────────── │  Wi-Fi Roulette Hub  │
  └──────────────────┘     (on 0h Remaining BUST)  └──────────────────────┘
```

### 📡 1. Automated Zero-Config Network Radar
- **Instant LAN Discovery:** Automatically scans ARP tables and resolves reverse DNS directly through your gateway cache.
- **OUI Vendor Fingerprinting:** Identifies Apple, Ubiquiti, Espressif, Google, Sony PlayStation, Nintendo, Samsung, Ring, and Amazon devices.
- **Device Avatar & Categorization:** Automatically classifies smartphones, laptops, desktops, gaming consoles, smart cameras, and IoT equipment.
- **Immunity Shield:** The default network gateway (`192.168.1.1`) and the host machine running the server are **automatically marked as PROTECTED** so you can never accidentally cut off your router or yourself.

### 🎡 2. Authentic European Roulette Floor
- **Physics-Simulated Wheel:** Full HTML5 Canvas 2D/3D single-zero European wheel (`0` to `36`) with realistic momentum, ball fret collisions, hopping, and zero-drift pocket settling.
- **Interactive Betting Felt:** Drag physical time tokens or click betting zones directly on the green felt table.
- **Complete Casino Bets:**
  - **Red / Black** (1:1 payout — double your hours)
  - **Even / Odd** (1:1 payout)
  - **Low / High (1–18 / 19–36)** (1:1 payout)
  - **Dozens (1st 12, 2nd 12, 3rd 12)** (2:1 payout)
  - **Columns (Col 1, Col 2, Col 3)** (2:1 payout)
  - **Straight-Up Numbers (`0` to `36`)** (35:1 payout — 36x your wagered time!)
- **Quick Action Triggers:** One-click shortcuts for `ALL-IN RED`, `ALL-IN BLACK`, `2X DOUBLE`, and `CLEAR`.

### 🔊 3. Zero-Asset Procedural Web Audio Synth
- 100% synthesized in real time directly inside the browser using the Web Audio API.
- **Zero MP3 / WAV files needed** — ultra-lightweight, zero latency, and runs completely offline.
- Features:
  - Dynamic clay chip clacks and stacking sounds
  - Realistic ceramic ball whir and fret clicks
  - Tense, rising heartbeat oscillator when betting high stakes
  - Retro arcade victory arpeggios
  - Power-down alarm klaxon on BUST

### 🔌 4. Pluggable Wi-Fi Enforcement Drivers
| Driver | Mechanism | Best For |
|---|---|---|
| **🧪 Simulation Mode** (Default) | In-memory & DB status logging with audio/visual warnings. | Testing, demos, harmless fun. |
| **📡 UniFi Gateway API** | Native UniFi Controller STA manager (`block-sta` / `unblock-sta`). | UniFi Dream Machine, UDR, Cloud Gateway Ultra, UDM-Pro. |
| **🛡️ Windows Firewall** | Inbound & Outbound block rules via `netsh advfirewall`. | Windows host networks and local subnet enforcement. |
| **⚡ Custom Webhook / SSH** | Arbitrary shell script or HTTP POST with `{mac}`, `{ip}`, `{hostname}`. | Home Assistant, Pi-hole, pfSense, OpenWrt, MikroTik, or remote SSH commands. |

### 👨‍⚖️ 5. Parental & Admin Control
- **Admin Emergency Pardon:** PIN-protected admin action (`1234` default) to instantly pardon any locked-out device, restore its Wi-Fi access, and award grace hours.
- **Manual Cutoff:** Test-fire Wi-Fi termination on demand to verify router blocking rules.
- **Live Monthly Ticker:** Live countdown clock showing days, hours, minutes, and seconds until the next monthly reset cycle (1st of each month).

---

## 📊 Mathematical Odds & Payout Table

Built according to standard European single-zero roulette odds (House Edge: **2.70%**):

| Bet Type | Example Selection | Numbers Covered | Payout Multiplier | Win Probability |
|:---|:---|:---:|:---:|:---:|
| **Straight Up** | `0`, `7`, `17`, `32` | 1 | **35:1** (36x return) | 2.70% |
| **Red / Black** | `Red`, `Black` | 18 | **1:1** (2x return) | 48.65% |
| **Even / Odd** | `Even`, `Odd` | 18 | **1:1** (2x return) | 48.65% |
| **Low / High** | `1-18`, `19-36` | 18 | **1:1** (2x return) | 48.65% |
| **Dozens** | `1st 12`, `2nd 12`, `3rd 12` | 12 | **2:1** (3x return) | 32.43% |
| **Columns** | `Col 1`, `Col 2`, `Col 3` | 12 | **2:1** (3x return) | 32.43% |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- Windows, Linux, or macOS

### 1. Clone the Repository
```bash
git clone https://github.com/ThomasConway01/wifi-gambling.git
cd wifi-gambling
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the Server

**On Windows (1-Click):**
```powershell
.\start.ps1
```
*or double-click `run.bat`*

**On Linux / macOS:**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Open the Casino
Navigate to:
```
http://localhost:8000
```

---

## ⚙️ Router Configuration Guides

### 📡 Ubiquiti UniFi Setup (Dream Machine / UDR / Gateway)
1. Open the web interface at `http://localhost:8000` and click **⚙️ Settings** in the top-right corner.
2. Select **📡 UniFi Controller API** under *Wi-Fi Enforcement Engine*.
3. Configure your controller connection:
   - **Host URL:** `https://192.168.1.1` (or your UniFi Gateway IP)
   - **Username & Password:** Your local UniFi admin credentials.
   - **Site:** `default`
4. Click **Test Enforcement Connection**. Once confirmed, click **Save & Apply Settings**.
5. When a device busts out, the app sends an instantaneous `block-sta` API command directly to your access points!

### ⚡ Custom Webhook / SSH / Home Assistant
Under Settings, select **⚡ Custom Shell Command / HTTP Webhook**:
- **Block Command Template:**
  ```bash
  ssh admin@192.168.1.1 "/usr/sbin/iptables -I FORWARD -m mac --mac-source {mac} -j DROP"
  ```
- **Unblock Command Template:**
  ```bash
  ssh admin@192.168.1.1 "/usr/sbin/iptables -D FORWARD -m mac --mac-source {mac} -j DROP"
  ```
Or trigger a Home Assistant webhook:
```
https://homeassistant.local:8123/api/webhook/wifi_block_{mac}
```

---

## 🧪 Running Automated Tests

A comprehensive test suite covers European roulette mathematical odds, payout multipliers, device immunity shields, BUST cutoff enforcement, and admin pardons:

```bash
python -m unittest discover tests
```

Output:
```text
.............
----------------------------------------------------------------------
Ran 13 tests in 0.266s

OK
✓ Static frontend assets loaded successfully.
✓ Discovered 25 devices (2 protected).
✓ Protected device immunity verified.
✓ Spin WON! Landed on 21 Red. Balance increased by 2.0h.
✓ Wi-Fi CUTOFF verified! Device locked out on bust.
✓ Admin Pardon verified! Wi-Fi restored.
✓ Enforcement driver verified: Simulation driver is active and ready.
```

---

## 🔒 Security & Privacy

- **Zero Baked-in Secrets:** The codebase contains zero hardcoded API keys, private credentials, or home network dumps.
- **Local-First Architecture:** The database and web server run 100% locally on your machine. No telemetry or telemetry pings to external servers.
- **Fail-Safe Protection:** Gateways, DNS hosts, and the server host are protected against lockouts by default.
- **Simulation First:** Defaults to Simulation mode out-of-the-box so you can experiment without risking unwanted internet drops.

---

## 📜 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more details.

---

<p align="center">
  <i>🎰 Remember: The house always has a 2.70% edge. Gamble your bandwidth responsibly.</i>
</p>
