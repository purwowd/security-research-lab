#!/usr/bin/env python3
"""
GSM RACH Flooding PoC - Anti-IMSI Catcher Defense
==================================================

Defensive tool to protect against fake BTS IMSI catchers by flooding
the RACH (Random Access Channel) with continuous access bursts, preventing
the fake BTS from processing legitimate phone connections.

Category: RF & Wireless - GSM Defense
Author: Security Research Lab
Version: 1.0.0
Date: 2026-02-12

Description:
    This PoC generates continuous RACH (Random Access Channel) bursts to
    overload a fake BTS system. By saturating the uplink with access requests,
    the fake BTS cannot process legitimate IMSI capture attempts from real
    mobile devices.

Hardware Requirements:
    - SDR capable of GSM transmission (HackRF One, BladeRF, USRP B210)
    - Antenna for GSM band (900/1800 MHz)
    - **FARADAY CAGE REQUIRED** - This transmits RF signals

Legal:
    Authorized security testing only. See 02_LEGAL_CONTEXT.md.
    RF transmission requires appropriate licensing and shielded environment.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import argparse
import json
import logging
import sys
import time
import traceback
import struct
import random

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

VULN_INFO = {
    "name": "GSM RACH Flooding - Anti-IMSI Catcher Defense",
    "cve": "N/A",
    "cwe": "N/A",
    "severity": "INFO",
    "cvss_score": 0.0,
    "cvss_vector": "N/A",
    "affected_software": "Fake BTS / IMSI Catchers",
    "affected_versions": "All GSM 2G fake BTS implementations",
    "fixed_version": "N/A",
    "description": "Defensive technique to overload fake BTS RACH processing by flooding with access bursts",
    "impact": "Prevents fake BTS from capturing IMSI from legitimate mobile devices",
    "attack_vector": "Adjacent",
    "authentication": "None",
    "author": "Security Research Lab",
    "date": "2026-02-12",
    "references": [
        "https://en.wikipedia.org/wiki/Random-access_channel",
        "https://www.etsi.org/deliver/etsi_ts/144000_144099/144018/",
    ],
}


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────

class PocResult(str, Enum):
    """PoC execution results."""
    VULNERABLE = "VULNERABLE"
    NOT_VULNERABLE = "NOT_VULNERABLE"
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"


class Severity(str, Enum):
    """Severity levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


# ──────────────────────────────────────────────
# Logging with PoC conventions
# ──────────────────────────────────────────────

class PocFormatter(logging.Formatter):
    """PoC-style log formatter using security convention symbols."""

    SYMBOLS = {
        logging.DEBUG: "\033[36m[D]\033[0m",
        logging.INFO: "\033[37m[*]\033[0m",
        logging.WARNING: "\033[33m[!]\033[0m",
        logging.ERROR: "\033[31m[-]\033[0m",
        logging.CRITICAL: "\033[1;31m[!!]\033[0m",
    }

    SUCCESS = 25
    ACTION = 15

    def format(self, record: logging.LogRecord) -> str:
        if record.levelno == self.SUCCESS:
            symbol = "\033[32m[+]\033[0m"
        elif record.levelno == self.ACTION:
            symbol = "\033[35m[>]\033[0m"
        else:
            symbol = self.SYMBOLS.get(record.levelno, "[?]")

        return f"{symbol} {record.getMessage()}"


def setup_poc_logging(verbose: bool = False) -> logging.Logger:
    """Setup PoC-style logging."""
    logger = logging.getLogger("poc")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    logging.addLevelName(PocFormatter.SUCCESS, "SUCCESS")
    logging.addLevelName(PocFormatter.ACTION, "ACTION")

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(PocFormatter())
    logger.addHandler(handler)

    def success(self, message, *args, **kwargs):
        self.log(PocFormatter.SUCCESS, message, *args, **kwargs)

    def action(self, message, *args, **kwargs):
        self.log(PocFormatter.ACTION, message, *args, **kwargs)

    logger.success = success.__get__(logger)
    logger.action = action.__get__(logger)

    return logger


logger = setup_poc_logging()


# ──────────────────────────────────────────────
# GSM RACH Burst Generator
# ──────────────────────────────────────────────

class GSMRACHBurst:
    """GSM RACH (Random Access Channel) burst generator."""
    
    # RACH burst parameters (GSM 05.02)
    RACH_BURST_LENGTH = 88  # bits (8 sync + 41 training + 36 data + 3 tail)
    TRAINING_SEQUENCE = [0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0]
    
    def __init__(self):
        self.burst_count = 0
    
    def generate_rach_burst(self, reference: int = None) -> bytes:
        """
        Generate a GSM RACH burst.
        
        Args:
            reference: Optional RACH reference (0-255), random if None
        
        Returns:
            Raw RACH burst data
        """
        if reference is None:
            reference = random.randint(0, 255)
        
        # RACH burst structure:
        # - 8 bits: Extended tail bits (all 0)
        # - 41 bits: Synchronization sequence (training sequence)
        # - 36 bits: Information bits (8 bits data + 5 bits BSIC + 23 bits padding)
        # - 3 bits: Tail bits (all 0)
        
        burst = []
        
        # Extended tail (8 bits)
        burst.extend([0] * 8)
        
        # Training sequence (41 bits)
        burst.extend(self.TRAINING_SEQUENCE)
        
        # Information bits (36 bits)
        # 8-bit RACH reference
        for i in range(7, -1, -1):
            burst.append((reference >> i) & 1)
        
        # BSIC (5 bits) - randomized
        bsic = random.randint(0, 31)
        for i in range(4, -1, -1):
            burst.append((bsic >> i) & 1)
        
        # Padding (23 bits) - randomized to avoid pattern detection
        for _ in range(23):
            burst.append(random.randint(0, 1))
        
        # Tail bits (3 bits)
        burst.extend([0] * 3)
        
        self.burst_count += 1
        
        # Convert bit array to bytes
        return self._bits_to_bytes(burst)
    
    def _bits_to_bytes(self, bits: list) -> bytes:
        """Convert bit array to bytes."""
        byte_array = bytearray()
        for i in range(0, len(bits), 8):
            byte_val = 0
            for j in range(min(8, len(bits) - i)):
                byte_val |= (bits[i + j] << (7 - j))
            byte_array.append(byte_val)
        return bytes(byte_array)


# ──────────────────────────────────────────────
# PoC Base Class
# ──────────────────────────────────────────────

class PocBase(ABC):
    """Base class for Proof-of-Concept implementations."""

    def __init__(self, target: str, options: dict | None = None):
        self.target = target
        self.options = options or {}
        self.vuln_info = VULN_INFO
        self.result = PocResult.UNKNOWN
        self.evidence: list[str] = []
        self.artifacts: list[str] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def print_banner(self):
        """Print PoC banner with vulnerability info."""
        v = self.vuln_info
        print()
        print("=" * 70)
        print(f" PoC: {v['name']}")
        print("=" * 70)
        print(f" Target ARFCN: {self.target}")
        print(f" Purpose:      {v['description']}")
        print(f" Impact:       {v['impact']}")
        print(f" Author:       {v['author']}")
        print(f" Date:         {v['date']}")
        print("=" * 70)
        print()

    @abstractmethod
    def check(self) -> bool:
        """Non-destructive check if the target is vulnerable."""
        pass

    @abstractmethod
    def exploit(self) -> dict:
        """Demonstrate the vulnerability exploitation."""
        pass

    def verify(self, exploit_result: dict) -> bool:
        """Verify that exploitation was successful."""
        return exploit_result.get("success", False)

    def cleanup(self):
        """Clean up any artifacts from exploitation."""
        logger.info("Cleanup: Stopping transmission...")
        for artifact in self.artifacts:
            logger.debug(f"Cleaning up: {artifact}")

    def add_evidence(self, evidence: str):
        """Add evidence of vulnerability."""
        self.evidence.append(evidence)
        logger.debug(f"Evidence: {evidence}")

    def execute(self, mode: str = "check") -> dict:
        """Execute the PoC lifecycle."""
        self.start_time = datetime.now()
        self.print_banner()

        try:
            if mode == "check":
                logger.info("Mode: CHECK (non-destructive)")
                is_vulnerable = self.check()
                self.result = PocResult.VULNERABLE if is_vulnerable else PocResult.NOT_VULNERABLE

            elif mode == "exploit":
                logger.info("Mode: EXPLOIT")
                exploit_result = self.exploit()
                is_verified = self.verify(exploit_result)
                self.result = PocResult.VULNERABLE if is_verified else PocResult.ERROR

            elif mode == "full":
                logger.info("Mode: FULL (check + exploit + verify + cleanup)")
                
                logger.info("Phase 1: Checking...")
                is_vulnerable = self.check()
                
                if not is_vulnerable:
                    self.result = PocResult.NOT_VULNERABLE
                else:
                    logger.info("Phase 2: Exploiting...")
                    exploit_result = self.exploit()
                    
                    logger.info("Phase 3: Verifying...")
                    is_verified = self.verify(exploit_result)
                    self.result = PocResult.VULNERABLE if is_verified else PocResult.ERROR
                    
                    logger.info("Phase 4: Cleaning up...")
                    self.cleanup()

        except KeyboardInterrupt:
            logger.warning("Interrupted by user")
            self.result = PocResult.ERROR
            self.cleanup()
        except Exception as e:
            logger.error(f"Error: {e}")
            logger.debug(traceback.format_exc())
            self.result = PocResult.ERROR
        finally:
            self.end_time = datetime.now()

        self.print_summary()
        
        return {
            "result": self.result.value,
            "target": self.target,
            "evidence": self.evidence,
            "duration": (self.end_time - self.start_time).total_seconds(),
            "timestamp": self.start_time.isoformat(),
        }

    def print_summary(self):
        """Print execution summary."""
        duration = (self.end_time - self.start_time).total_seconds()
        
        print()
        print("=" * 70)
        print(" SUMMARY")
        print("=" * 70)
        
        severity_color = {
            PocResult.NOT_VULNERABLE: "\033[1;34m",
            PocResult.VULNERABLE: "\033[1;32m",
            PocResult.UNKNOWN: "\033[1;33m",
            PocResult.ERROR: "\033[1;35m",
        }
        color = severity_color.get(self.result, "\033[0m")
        print(f" Result: {color}{self.result.value}\033[0m")
        print(f" Duration: {duration:.2f}s")

        if self.evidence:
            print(f" Evidence:")
            for e in self.evidence:
                print(f"   - {e[:100]}")

        print("=" * 70)
        print()


# ──────────────────────────────────────────────
# RACH Flood PoC Implementation
# ──────────────────────────────────────────────

class RACHFloodPoC(PocBase):
    """
    GSM RACH Flooding PoC for anti-IMSI catcher defense.
    
    This PoC floods a fake BTS with continuous RACH bursts to prevent
    it from processing legitimate IMSI capture attempts.
    """

    def __init__(self, target: str, options: dict | None = None):
        super().__init__(target, options)
        self.arfcn = int(target)  # Target ARFCN
        self.burst_generator = GSMRACHBurst()
        self.sdr_available = self._check_sdr_availability()
        
    def _check_sdr_availability(self) -> bool:
        """Check if SDR hardware/software is available."""
        try:
            # Check for GNU Radio
            import gnuradio
            logger.debug("GNU Radio found")
            return True
        except ImportError:
            logger.warning("GNU Radio not found - simulation mode only")
            return False
    
    def _arfcn_to_frequency(self, arfcn: int) -> float:
        """
        Convert ARFCN to frequency in MHz.
        
        Args:
            arfcn: Absolute Radio Frequency Channel Number
        
        Returns:
            Frequency in MHz
        """
        # GSM-900 band
        if 0 <= arfcn <= 124:
            return 890.0 + 0.2 * arfcn  # Uplink
        # E-GSM-900
        elif 975 <= arfcn <= 1023:
            return 890.0 + 0.2 * (arfcn - 1024)  # Uplink
        # DCS-1800
        elif 512 <= arfcn <= 885:
            return 1710.0 + 0.2 * (arfcn - 512)  # Uplink
        else:
            raise ValueError(f"Invalid ARFCN: {arfcn}")
    
    def check(self) -> bool:
        """Check if the setup is ready for RACH flooding."""
        logger.action("Checking RACH flood prerequisites...")
        
        # Validate ARFCN
        try:
            freq = self._arfcn_to_frequency(self.arfcn)
            logger.success(f"Target ARFCN {self.arfcn} -> {freq:.1f} MHz (uplink)")
            self.add_evidence(f"Valid ARFCN: {self.arfcn} ({freq:.1f} MHz)")
        except ValueError as e:
            logger.error(f"Invalid ARFCN: {e}")
            return False
        
        # Check SDR availability
        if self.sdr_available:
            logger.success("SDR software available (GNU Radio)")
            self.add_evidence("GNU Radio available for transmission")
        else:
            logger.warning("SDR software not available - simulation mode")
            self.add_evidence("Running in simulation mode (no actual RF)")
        
        # Safety checks
        logger.warning("⚠️  SAFETY REMINDER:")
        logger.warning("    - RF transmission requires Faraday cage")
        logger.warning("    - Ensure proper licensing for RF transmission")
        logger.warning("    - Use minimal TX power in lab environment")
        
        faraday_cage = self.options.get("faraday_cage_confirmed", False)
        if not faraday_cage:
            logger.error("Faraday cage not confirmed - aborting for safety")
            logger.error("Use --faraday-cage-confirmed to proceed")
            return False
        
        logger.success("Faraday cage confirmed")
        self.add_evidence("Faraday cage safety confirmed")
        
        return True
    
    def exploit(self) -> dict:
        """Execute RACH flooding attack."""
        logger.action(f"Starting RACH flood on ARFCN {self.arfcn}...")
        
        freq = self._arfcn_to_frequency(self.arfcn)
        duration = self.options.get("duration", 60)
        burst_rate = self.options.get("burst_rate", 100)  # bursts per second
        tx_power = self.options.get("tx_power", -10)  # dBm
        
        logger.info(f"Frequency: {freq:.1f} MHz (uplink)")
        logger.info(f"Duration: {duration} seconds")
        logger.info(f"Burst rate: {burst_rate} bursts/sec")
        logger.info(f"TX power: {tx_power} dBm")
        
        if self.sdr_available and self.options.get("hardware_mode", False):
            return self._execute_hardware_flood(freq, duration, burst_rate, tx_power)
        else:
            return self._execute_simulation_flood(freq, duration, burst_rate)
    
    def _execute_simulation_flood(self, freq: float, duration: int, burst_rate: int) -> dict:
        """Execute RACH flood in simulation mode."""
        logger.info("Running in SIMULATION mode (no actual RF transmission)")
        logger.info("This demonstrates the burst generation logic")
        
        start_time = time.time()
        total_bursts = 0
        burst_interval = 1.0 / burst_rate
        
        logger.action("Generating RACH bursts...")
        
        try:
            while (time.time() - start_time) < duration:
                # Generate RACH burst
                burst = self.burst_generator.generate_rach_burst()
                total_bursts += 1
                
                # Progress update every second
                if total_bursts % burst_rate == 0:
                    elapsed = time.time() - start_time
                    logger.info(f"Bursts sent: {total_bursts} | Elapsed: {elapsed:.1f}s")
                
                # Rate limiting
                time.sleep(burst_interval)
                
        except KeyboardInterrupt:
            logger.warning("Flood interrupted by user")
        
        elapsed = time.time() - start_time
        actual_rate = total_bursts / elapsed if elapsed > 0 else 0
        
        logger.success(f"RACH flood completed")
        logger.success(f"Total bursts: {total_bursts}")
        logger.success(f"Actual rate: {actual_rate:.1f} bursts/sec")
        logger.success(f"Duration: {elapsed:.1f} seconds")
        
        self.add_evidence(f"Generated {total_bursts} RACH bursts")
        self.add_evidence(f"Burst rate: {actual_rate:.1f} bursts/sec")
        self.add_evidence(f"Target frequency: {freq:.1f} MHz")
        
        return {
            "success": True,
            "bursts_sent": total_bursts,
            "duration": elapsed,
            "burst_rate": actual_rate,
            "frequency": freq,
            "mode": "simulation",
        }
    
    def _execute_hardware_flood(self, freq: float, duration: int, burst_rate: int, tx_power: int) -> dict:
        """Execute RACH flood with actual SDR hardware."""
        logger.warning("HARDWARE MODE - Actual RF transmission")
        logger.warning("Ensure Faraday cage is properly sealed!")
        
        try:
            from gnuradio import gr, blocks, analog
            from osmosdr import source as osmo_source, sink as osmo_sink
        except ImportError:
            logger.error("GNU Radio or gr-osmosdr not available")
            return {"success": False, "error": "Missing dependencies"}
        
        logger.info("Initializing SDR for transmission...")
        
        # This is a placeholder for actual GNU Radio flowgraph
        # In production, you would build a complete GSM transmitter flowgraph
        
        logger.warning("Hardware transmission not fully implemented in this PoC")
        logger.warning("Use simulation mode or implement full GNU Radio flowgraph")
        logger.warning("Refer to gr-gsm and OpenBTS for complete GSM stack")
        
        self.add_evidence("Hardware mode attempted (not fully implemented)")
        
        return {
            "success": False,
            "error": "Hardware mode requires full GNU Radio flowgraph implementation",
            "recommendation": "Use simulation mode or integrate with gr-gsm",
        }
    
    def verify(self, exploit_result: dict) -> bool:
        """Verify RACH flood execution."""
        if not exploit_result.get("success"):
            return False
        
        bursts_sent = exploit_result.get("bursts_sent", 0)
        logger.info(f"Verification: {bursts_sent} bursts generated")
        
        if bursts_sent > 0:
            logger.success("RACH flood executed successfully")
            return True
        
        return False
    
    def cleanup(self):
        """Clean up after RACH flood."""
        logger.info("Cleanup: Stopping RACH transmission...")
        logger.info("Cleanup: Releasing SDR resources...")
        super().cleanup()


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def create_poc_parser() -> argparse.ArgumentParser:
    """Create standard PoC argument parser."""
    parser = argparse.ArgumentParser(
        description=f"PoC: {VULN_INFO['name']}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simulation mode (no RF transmission)
  %(prog)s 62 --mode exploit --duration 30
  
  # With Faraday cage confirmation
  %(prog)s 62 --mode full --faraday-cage-confirmed --duration 60
  
  # Custom burst rate
  %(prog)s 62 --mode exploit --burst-rate 200 --duration 30

ARFCN Examples:
  - GSM-900: 0-124 (890-915 MHz uplink)
  - DCS-1800: 512-885 (1710-1785 MHz uplink)

⚠️  WARNING: RF transmission requires:
  - Faraday cage or RF shielded environment
  - Appropriate licensing
  - Minimal TX power for lab testing
        """,
    )

    parser.add_argument(
        "target",
        help="Target ARFCN (Absolute Radio Frequency Channel Number)",
    )

    parser.add_argument(
        "--mode",
        choices=["check", "exploit", "full"],
        default="check",
        help="Execution mode (default: check)",
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Flood duration in seconds (default: 60)",
    )

    parser.add_argument(
        "--burst-rate",
        type=int,
        default=100,
        help="RACH bursts per second (default: 100)",
    )

    parser.add_argument(
        "--tx-power",
        type=int,
        default=-10,
        help="TX power in dBm (default: -10, keep low for lab)",
    )

    parser.add_argument(
        "--faraday-cage-confirmed",
        action="store_true",
        help="Confirm Faraday cage is in use (REQUIRED for safety)",
    )

    parser.add_argument(
        "--hardware-mode",
        action="store_true",
        help="Use actual SDR hardware (requires GNU Radio + gr-osmosdr)",
    )

    parser.add_argument(
        "--output",
        help="Save results to file (JSON)",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )

    return parser


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

if __name__ == "__main__":
    parser = create_poc_parser()
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Create and execute PoC
    poc = RACHFloodPoC(
        target=args.target,
        options={
            "duration": args.duration,
            "burst_rate": args.burst_rate,
            "tx_power": args.tx_power,
            "faraday_cage_confirmed": args.faraday_cage_confirmed,
            "hardware_mode": args.hardware_mode,
            "verbose": args.verbose,
        },
    )

    result = poc.execute(mode=args.mode)

    # Save results
    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2, default=str)
        logger.info(f"Results saved to {args.output}")

    # Exit code
    sys.exit(0 if result["result"] in ["VULNERABLE", "UNKNOWN"] else 1)
