#!/usr/bin/env python3
"""
Fake BTS (Base Transceiver Station) Band Detector
Detects rogue/fake cell towers and identifies their transmission frequency bands

This script scans for cellular signals and identifies suspicious BTS by analyzing:
- Signal strength anomalies
- LAC/CID patterns
- Frequency bands used
- Encryption status

Requires RTL-SDR or similar SDR hardware for signal detection.
"""

import argparse
import sys
import time
from datetime import datetime
from collections import defaultdict

try:
    from rtlsdr import RtlSdr
    import numpy as np
except ImportError:
    print("Warning: rtlsdr not available. Running in simulation mode.")
    RtlSdr = None
    np = None


class GSMBandInfo:
    """GSM frequency band definitions"""
    BANDS = {
        'GSM-850': {
            'uplink': (824.0, 849.0),
            'downlink': (869.0, 894.0),
            'arfcn_range': (128, 251),
            'region': 'Americas'
        },
        'GSM-900': {
            'uplink': (890.0, 915.0),
            'downlink': (935.0, 960.0),
            'arfcn_range': (0, 124),
            'region': 'Europe, Asia, Africa'
        },
        'E-GSM-900': {
            'uplink': (880.0, 915.0),
            'downlink': (925.0, 960.0),
            'arfcn_range': (975, 1023),
            'region': 'Europe Extended'
        },
        'DCS-1800': {
            'uplink': (1710.0, 1785.0),
            'downlink': (1805.0, 1880.0),
            'arfcn_range': (512, 885),
            'region': 'Europe, Asia'
        },
        'PCS-1900': {
            'uplink': (1850.0, 1910.0),
            'downlink': (1930.0, 1990.0),
            'arfcn_range': (512, 810),
            'region': 'Americas'
        }
    }
    
    LTE_BANDS = {
        'Band 1': (2100, 'FDD', 'Europe, Asia'),
        'Band 3': (1800, 'FDD', 'Europe, Asia'),
        'Band 7': (2600, 'FDD', 'Europe, Asia'),
        'Band 8': (900, 'FDD', 'Europe, Asia'),
        'Band 20': (800, 'FDD', 'Europe'),
        'Band 28': (700, 'FDD', 'Asia-Pacific'),
        'Band 40': (2300, 'TDD', 'Asia'),
        'Band 41': (2500, 'TDD', 'Global')
    }

    @staticmethod
    def freq_to_band(freq_mhz):
        """Determine GSM band from frequency"""
        for band_name, info in GSMBandInfo.BANDS.items():
            if info['downlink'][0] <= freq_mhz <= info['downlink'][1]:
                return band_name, info['region']
            if info['uplink'][0] <= freq_mhz <= info['uplink'][1]:
                return f"{band_name} (Uplink)", info['region']
        
        for band_name, (freq, mode, region) in GSMBandInfo.LTE_BANDS.items():
            if abs(freq_mhz - freq) < 100:
                return f"LTE {band_name}", region
        
        return "Unknown", "Unknown"

    @staticmethod
    def arfcn_to_freq(arfcn):
        """Convert ARFCN to frequency in MHz"""
        if 0 <= arfcn <= 124:
            return 935.0 + 0.2 * arfcn
        elif 128 <= arfcn <= 251:
            return 869.0 + 0.2 * (arfcn - 128)
        elif 512 <= arfcn <= 885:
            return 1805.0 + 0.2 * (arfcn - 512)
        elif 975 <= arfcn <= 1023:
            return 925.0 + 0.2 * (arfcn - 1024)
        return None


class FakeBTSDetector:
    """Detects and analyzes fake BTS stations"""
    
    def __init__(self, use_sdr=True, verbose=False):
        self.use_sdr = use_sdr and RtlSdr is not None
        self.verbose = verbose
        self.detected_cells = []
        self.suspicious_patterns = defaultdict(int)
        
    def scan_frequency_range(self, start_freq, end_freq, step=0.2):
        """Scan a frequency range for BTS signals"""
        print(f"\n[*] Scanning {start_freq:.1f} - {end_freq:.1f} MHz...")
        
        if self.use_sdr:
            return self._scan_with_sdr(start_freq, end_freq, step)
        else:
            return self._simulate_scan(start_freq, end_freq, step)
    
    def _scan_with_sdr(self, start_freq, end_freq, step):
        """Scan using RTL-SDR hardware"""
        sdr = RtlSdr()
        sdr.sample_rate = 2.048e6
        sdr.gain = 'auto'
        
        detections = []
        current_freq = start_freq
        
        while current_freq <= end_freq:
            sdr.center_freq = current_freq * 1e6
            samples = sdr.read_samples(256 * 1024)
            
            power = np.abs(samples) ** 2
            avg_power = np.mean(power)
            max_power = np.max(power)
            
            if max_power > avg_power * 10:
                band, region = GSMBandInfo.freq_to_band(current_freq)
                detections.append({
                    'frequency': current_freq,
                    'power': float(max_power),
                    'band': band,
                    'region': region,
                    'timestamp': datetime.now()
                })
                
                if self.verbose:
                    print(f"  [+] Signal detected at {current_freq:.2f} MHz ({band})")
            
            current_freq += step
        
        sdr.close()
        return detections
    
    def _simulate_scan(self, start_freq, end_freq, step):
        """Simulate scan for demonstration (no hardware required)"""
        import random
        
        detections = []
        
        simulated_signals = [
            (945.0, 'GSM-900', 'Europe, Asia, Africa', -65, False),
            (947.4, 'GSM-900', 'Europe, Asia, Africa', -70, False),
            (1842.6, 'DCS-1800', 'Europe, Asia', -68, True),
            (2142.0, 'LTE Band 1', 'Europe, Asia', -72, True),
        ]
        
        for freq, band, region, power, is_suspicious in simulated_signals:
            if start_freq <= freq <= end_freq:
                detection = {
                    'frequency': freq,
                    'power': power,
                    'band': band,
                    'region': region,
                    'timestamp': datetime.now(),
                    'lac': random.randint(1, 65535) if is_suspicious else random.randint(100, 1000),
                    'cid': random.randint(1, 65535),
                    'mcc': 510 if is_suspicious else 510,
                    'mnc': 99 if is_suspicious else 10,
                    'encryption': 'A5/0' if is_suspicious else 'A5/1',
                    'is_suspicious': is_suspicious
                }
                detections.append(detection)
                
                if self.verbose:
                    print(f"  [+] Signal at {freq:.2f} MHz ({band}) - Power: {power} dBm")
        
        time.sleep(1)
        return detections
    
    def analyze_cell(self, cell_info):
        """Analyze a cell for suspicious characteristics"""
        suspicion_score = 0
        reasons = []
        
        if cell_info.get('encryption') == 'A5/0':
            suspicion_score += 30
            reasons.append("No encryption (A5/0)")
        
        if cell_info.get('power', 0) > -50:
            suspicion_score += 20
            reasons.append("Unusually high signal strength")
        
        lac = cell_info.get('lac', 0)
        if lac > 60000 or lac == 1:
            suspicion_score += 25
            reasons.append(f"Suspicious LAC: {lac}")
        
        if cell_info.get('mnc') == 99:
            suspicion_score += 15
            reasons.append("Test network MNC (99)")
        
        return suspicion_score, reasons
    
    def scan_all_gsm_bands(self):
        """Scan all common GSM/LTE bands"""
        print("\n" + "="*70)
        print("FAKE BTS DETECTOR - Frequency Band Scanner")
        print("="*70)
        
        all_detections = []
        
        bands_to_scan = [
            ('GSM-900', 935.0, 960.0),
            ('DCS-1800', 1805.0, 1880.0),
            ('LTE 2100', 2100.0, 2170.0),
        ]
        
        for band_name, start, end in bands_to_scan:
            print(f"\n[*] Scanning {band_name} band...")
            detections = self.scan_frequency_range(start, end, step=2.0)
            all_detections.extend(detections)
        
        return all_detections
    
    def generate_report(self, detections):
        """Generate detection report"""
        print("\n" + "="*70)
        print("DETECTION REPORT")
        print("="*70)
        
        if not detections:
            print("\n[!] No signals detected.")
            return
        
        print(f"\n[*] Total signals detected: {len(detections)}")
        
        suspicious_cells = []
        normal_cells = []
        
        for cell in detections:
            score, reasons = self.analyze_cell(cell)
            cell['suspicion_score'] = score
            cell['suspicion_reasons'] = reasons
            
            if score >= 40:
                suspicious_cells.append(cell)
            else:
                normal_cells.append(cell)
        
        if suspicious_cells:
            print(f"\n[!] SUSPICIOUS BTS DETECTED: {len(suspicious_cells)}")
            print("-" * 70)
            
            for i, cell in enumerate(suspicious_cells, 1):
                print(f"\n  [{i}] Suspicious Cell:")
                print(f"      Frequency: {cell['frequency']:.2f} MHz")
                print(f"      Band: {cell['band']}")
                print(f"      Region: {cell['region']}")
                print(f"      Power: {cell.get('power', 'N/A')} dBm")
                print(f"      Suspicion Score: {cell['suspicion_score']}/100")
                print(f"      Reasons:")
                for reason in cell['suspicion_reasons']:
                    print(f"        - {reason}")
                if 'lac' in cell:
                    print(f"      LAC: {cell['lac']}, CID: {cell['cid']}")
                    print(f"      MCC/MNC: {cell['mcc']}/{cell['mnc']}")
                    print(f"      Encryption: {cell['encryption']}")
        
        if normal_cells:
            print(f"\n[*] Normal BTS detected: {len(normal_cells)}")
            print("-" * 70)
            
            for i, cell in enumerate(normal_cells, 1):
                print(f"\n  [{i}] Normal Cell:")
                print(f"      Frequency: {cell['frequency']:.2f} MHz")
                print(f"      Band: {cell['band']}")
                print(f"      Region: {cell['region']}")
                print(f"      Power: {cell.get('power', 'N/A')} dBm")
        
        print("\n" + "="*70)
        print("BAND SUMMARY")
        print("="*70)
        
        band_counts = defaultdict(int)
        for cell in detections:
            band_counts[cell['band']] += 1
        
        for band, count in sorted(band_counts.items()):
            print(f"  {band}: {count} signal(s)")
        
        print("\n" + "="*70)


def main():
    parser = argparse.ArgumentParser(
        description='Fake BTS Detector - Identify rogue cell towers and their frequency bands'
    )
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose output')
    parser.add_argument('-s', '--simulate', action='store_true',
                        help='Run in simulation mode (no SDR required)')
    parser.add_argument('-f', '--frequency', type=float,
                        help='Scan specific frequency (MHz)')
    parser.add_argument('-r', '--range', nargs=2, type=float, metavar=('START', 'END'),
                        help='Scan frequency range (MHz)')
    
    args = parser.parse_args()
    
    use_sdr = not args.simulate
    detector = FakeBTSDetector(use_sdr=use_sdr, verbose=args.verbose)
    
    if args.frequency:
        freq = args.frequency
        band, region = GSMBandInfo.freq_to_band(freq)
        print(f"\n[*] Frequency: {freq} MHz")
        print(f"[*] Band: {band}")
        print(f"[*] Region: {region}")
        detections = detector.scan_frequency_range(freq - 5, freq + 5, step=0.2)
    elif args.range:
        start, end = args.range
        detections = detector.scan_frequency_range(start, end, step=0.5)
    else:
        detections = detector.scan_all_gsm_bands()
    
    detector.generate_report(detections)
    
    print("\n[*] Scan complete.")
    print("\n[!] WARNING: This tool is for security research and authorized testing only.")


if __name__ == '__main__':
    main()
