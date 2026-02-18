# GSM RACH Flooding PoC - Anti-IMSI Catcher Defense

## Overview

This PoC demonstrates a defensive technique against fake BTS IMSI catchers by flooding the Random Access Channel (RACH) with continuous access bursts. By saturating the uplink channel, the fake BTS becomes overloaded and cannot process legitimate IMSI capture attempts from real mobile devices.

## Vulnerability Details

| Field | Value |
|-------|-------|
| **Name** | GSM RACH Flooding - Anti-IMSI Catcher Defense |
| **Type** | Defensive Countermeasure |
| **Target** | Fake BTS / IMSI Catchers |
| **Impact** | Prevents IMSI capture from legitimate devices |
| **Attack Vector** | Adjacent (RF transmission) |

## Technical Background

### RACH (Random Access Channel)

The RACH is used by mobile devices to initiate contact with the base station. Key characteristics:

- **Uplink only** channel (mobile → BTS)
- **Contention-based** access (no coordination)
- **Limited processing capacity** on BTS side
- Used for initial access requests, location updates, emergency calls

### Attack Principle

1. Fake BTS broadcasts as legitimate cell tower
2. Mobile devices attempt to connect via RACH
3. Fake BTS captures IMSI during authentication
4. **Defense**: Flood RACH with continuous bursts → BTS overload → Cannot process real devices

### RACH Burst Structure

```
┌─────────────┬──────────────┬─────────────────┬──────────┐
│ Tail (8bit) │ Sync (41bit) │ Data (36bit)    │ Tail (3) │
└─────────────┴──────────────┴─────────────────┴──────────┘
                                │
                                ├─ 8-bit: RACH reference
                                ├─ 5-bit: BSIC
                                └─ 23-bit: Padding
```

## Hardware Requirements

### Minimum (Simulation Mode)
- Python 3.10+
- No SDR hardware required

### Full Implementation (Hardware Mode)
- **SDR Device**: HackRF One, BladeRF 2.0, or USRP B210
- **Antenna**: GSM band (900/1800 MHz)
- **Faraday Cage**: **MANDATORY** for RF transmission
- **Software**: GNU Radio 3.10+, gr-osmosdr

### Recommended SDR Hardware

| Device | Frequency Range | TX Power | Use Case |
|--------|----------------|----------|----------|
| HackRF One | 1 MHz - 6 GHz | ~10 dBm | Budget option, good for testing |
| BladeRF 2.0 | 47 MHz - 6 GHz | ~6 dBm | Better performance, USB 3.0 |
| USRP B210 | 70 MHz - 6 GHz | ~10 dBm | Professional grade, best quality |

## Installation

### Python Dependencies

```bash
pip install -r requirements.txt
```

### GNU Radio (Optional - for hardware mode)

```bash
# Ubuntu/Debian
sudo apt-get install gnuradio gr-osmosdr

# Arch Linux
sudo pacman -S gnuradio gnuradio-osmosdr

# From source
git clone https://github.com/gnuradio/gnuradio.git
cd gnuradio
mkdir build && cd build
cmake ..
make -j$(nproc)
sudo make install
```

## Usage

### Basic Usage (Simulation Mode)

```bash
# Check prerequisites
python poc_rach_flood.py 62 --mode check

# Run RACH flood simulation (no RF transmission)
python poc_rach_flood.py 62 --mode exploit --duration 30

# Full lifecycle with Faraday cage confirmation
python poc_rach_flood.py 62 --mode full --faraday-cage-confirmed --duration 60
```

### Advanced Options

```bash
# High burst rate (200 bursts/sec)
python poc_rach_flood.py 62 --mode exploit --burst-rate 200 --duration 30

# Custom TX power (hardware mode)
python poc_rach_flood.py 62 --mode exploit --tx-power -15 --hardware-mode

# Save results to JSON
python poc_rach_flood.py 62 --mode exploit --output results.json

# Verbose output
python poc_rach_flood.py 62 --mode exploit -v
```

### ARFCN Reference

Common GSM ARFCNs:

| Band | ARFCN Range | Uplink Frequency | Region |
|------|-------------|------------------|--------|
| GSM-900 | 0-124 | 890-915 MHz | Europe, Asia, Africa |
| E-GSM-900 | 975-1023 | 880-890 MHz | Extended GSM-900 |
| DCS-1800 | 512-885 | 1710-1785 MHz | Europe, Asia |
| PCS-1900 | 512-810 | 1850-1910 MHz | Americas |

Example ARFCNs:
- **ARFCN 62**: 902.4 MHz (GSM-900 uplink)
- **ARFCN 700**: 1750 MHz (DCS-1800 uplink)

## Safety & Legal Considerations

### ⚠️ CRITICAL SAFETY REQUIREMENTS

1. **Faraday Cage MANDATORY**
   - All RF transmission MUST occur in Faraday cage
   - No exceptions - uncontrolled RF transmission is illegal

2. **Licensing**
   - RF transmission requires appropriate spectrum licensing
   - Lab/research exemptions may apply in some jurisdictions
   - Consult local telecommunications authority

3. **Power Limits**
   - Keep TX power minimal (-10 dBm or lower)
   - Higher power increases interference risk
   - Lab testing should use lowest effective power

4. **Authorized Testing Only**
   - Only test on your own equipment
   - Never target operational cellular networks
   - Fake BTS testing requires controlled environment

### Legal Framework

This tool is designed for:
- **Authorized security research** in controlled lab environments
- **Defensive testing** of IMSI catcher detection systems
- **Educational purposes** demonstrating GSM security concepts

**Unauthorized use is illegal** under:
- US: Communications Act, FCC regulations
- EU: Radio Equipment Directive, national telecommunications laws
- Most jurisdictions: Telecommunications/radio spectrum regulations

## How It Works

### Phase 1: Check
- Validates target ARFCN
- Converts ARFCN to frequency
- Checks SDR software availability
- Verifies Faraday cage confirmation

### Phase 2: Exploit (RACH Flood)
- Generates continuous RACH bursts
- Each burst contains:
  - Random RACH reference (0-255)
  - Random BSIC (Base Station Identity Code)
  - Proper GSM RACH structure
- Transmits at specified burst rate (default: 100/sec)

### Phase 3: Verify
- Confirms burst generation
- Validates transmission parameters
- Reports statistics (bursts sent, rate, duration)

### Phase 4: Cleanup
- Stops transmission
- Releases SDR resources
- Reports artifacts

## Expected Results

### Simulation Mode
```
[*] Phase 1: Checking vulnerability...
[+] Target ARFCN 62 -> 902.4 MHz (uplink)
[+] SDR software available (GNU Radio)
[+] Faraday cage confirmed
[*] Phase 2: Exploiting...
[>] Starting RACH flood on ARFCN 62...
[*] Bursts sent: 100 | Elapsed: 1.0s
[*] Bursts sent: 200 | Elapsed: 2.0s
...
[+] RACH flood completed
[+] Total bursts: 3000
[+] Actual rate: 100.0 bursts/sec
```

### Impact on Fake BTS
- **RACH queue saturation**: Processing capacity exceeded
- **Legitimate devices blocked**: Cannot complete access requests
- **IMSI capture prevented**: No bandwidth for authentication
- **Fake BTS overload**: May crash or become unresponsive

## Limitations

1. **Simulation Mode**: No actual RF transmission, demonstrates logic only
2. **Hardware Mode**: Requires full GNU Radio flowgraph (not fully implemented)
3. **Range**: Limited to Faraday cage (by design for safety)
4. **Detection**: Fake BTS may implement flood detection/mitigation
5. **Effectiveness**: Depends on fake BTS processing capacity

## Countermeasures (For Fake BTS Operators)

If you're testing fake BTS resilience:

1. **Rate limiting**: Limit RACH processing per time window
2. **Pattern detection**: Identify repetitive/random RACH patterns
3. **Source filtering**: Track and blacklist flooding sources
4. **Capacity planning**: Increase RACH processing capacity
5. **Anomaly detection**: Monitor for unusual RACH traffic patterns

## Integration with Other Tools

### With gr-gsm
```bash
# Scan for fake BTS first
grgsm_scanner -b GSM900

# Then flood detected fake BTS ARFCN
python poc_rach_flood.py <detected_arfcn> --mode exploit
```

### With IMSI Catcher Detection Apps
- Use mobile app to detect fake BTS
- Note the ARFCN
- Deploy RACH flood on that ARFCN
- Verify IMSI catcher becomes non-functional

## Troubleshooting

### "GNU Radio not found"
- Install GNU Radio: `sudo apt-get install gnuradio`
- Or use simulation mode (no hardware needed)

### "Invalid ARFCN"
- Check ARFCN is in valid range (0-124, 512-885, 975-1023)
- Verify band matches your region

### "Faraday cage not confirmed"
- Add `--faraday-cage-confirmed` flag
- **Only if actually using Faraday cage**

### Low burst rate
- Increase `--burst-rate` parameter
- Check system performance (CPU usage)
- Hardware mode may have different limits

## References

- [3GPP TS 44.018](https://www.etsi.org/deliver/etsi_ts/144000_144099/144018/) - GSM Radio Resource Management
- [3GPP TS 45.002](https://www.etsi.org/deliver/etsi_ts/145000_145099/145002/) - GSM Physical Layer
- [gr-gsm](https://github.com/ptrkrysik/gr-gsm) - GNU Radio GSM implementation
- [IMSI Catcher Detection](https://github.com/CellularPrivacy/Android-IMSI-Catcher-Detector)

## Disclaimer

This tool is provided for authorized security research and educational purposes only. The authors are not responsible for misuse or illegal activities. Always comply with local laws and regulations regarding RF transmission and telecommunications security testing.

---

**Security Research Lab** | 2026-02-12
