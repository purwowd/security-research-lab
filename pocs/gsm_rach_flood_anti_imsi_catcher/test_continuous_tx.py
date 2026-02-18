#!/usr/bin/env python3
"""
Continuous Carrier Test - untuk verify USRP transmission
Transmit continuous carrier (CW) untuk mudah dilihat di spektrum analyzer
"""

import sys
import time
import logging
import argparse
import numpy as np

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

try:
    from gnuradio import gr, analog, uhd
    GNURADIO_AVAILABLE = True
except ImportError:
    GNURADIO_AVAILABLE = False
    logger.error("GNU Radio not available")
    sys.exit(1)


class ContinuousCarrier(gr.top_block):
    """Transmit continuous carrier for testing."""
    
    def __init__(self, frequency, sample_rate=2e6, tx_gain=20, amplitude=0.7):
        gr.top_block.__init__(self, "Continuous Carrier Test")
        
        logger.info("=" * 70)
        logger.info("Initializing USRP B210 for Continuous Carrier Test")
        logger.info(f"  Frequency: {frequency/1e6:.3f} MHz")
        logger.info(f"  Sample rate: {sample_rate/1e6:.1f} Msps")
        logger.info(f"  TX gain: {tx_gain} dB")
        logger.info(f"  Amplitude: {amplitude}")
        logger.info("=" * 70)
        
        # USRP Sink
        self.uhd_usrp_sink = uhd.usrp_sink(
            ",".join(("", "")),
            uhd.stream_args(
                cpu_format="fc32",
                channels=list(range(1)),
            ),
        )
        
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
        
        # Continuous sine wave source (0 Hz offset = carrier)
        self.analog_sig_source = analog.sig_source_c(
            sample_rate,
            analog.GR_COS_WAVE,
            0,  # 0 Hz offset = pure carrier
            amplitude,
            0
        )
        
        # Connect
        self.connect(self.analog_sig_source, self.uhd_usrp_sink)
        
        logger.info("Flowgraph connected - ready to transmit")


def main():
    parser = argparse.ArgumentParser(
        description="Continuous Carrier Test for USRP B210",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Test USRP transmission dengan continuous carrier (CW).
Ini akan mudah terlihat di spektrum analyzer.

Examples:
  # Test di 900.2 MHz dengan gain 20 dB
  python test_continuous_tx.py 900.2 --tx-gain 20 --duration 10
  
  # Test dengan gain lebih tinggi (30 dB)
  python test_continuous_tx.py 900.2 --tx-gain 30 --duration 5
  
  # Test di frequency lain
  python test_continuous_tx.py 945.2 --tx-gain 25 --duration 10

⚠️  WARNING: Ini transmit RF aktual!
   - Gunakan di dalam Faraday cage
   - Check di spektrum analyzer
        """
    )
    
    parser.add_argument("frequency", type=float, 
                       help="Frequency in MHz (e.g., 900.2)")
    parser.add_argument("--tx-gain", type=int, default=20,
                       help="TX gain in dB (0-89, default: 20)")
    parser.add_argument("--duration", type=int, default=10,
                       help="Transmission duration in seconds (default: 10)")
    parser.add_argument("--amplitude", type=float, default=0.7,
                       help="Signal amplitude 0-1 (default: 0.7)")
    parser.add_argument("--faraday-cage-confirmed", action="store_true",
                       help="Confirm Faraday cage (REQUIRED)")
    
    args = parser.parse_args()
    
    # Safety check
    if not args.faraday_cage_confirmed:
        logger.error("=" * 70)
        logger.error("SAFETY CHECK FAILED")
        logger.error("Add --faraday-cage-confirmed to proceed")
        logger.error("=" * 70)
        sys.exit(1)
    
    # Convert MHz to Hz
    freq_hz = args.frequency * 1e6
    
    logger.info("=" * 70)
    logger.info("CONTINUOUS CARRIER TEST")
    logger.info("=" * 70)
    logger.info(f"Frequency: {args.frequency} MHz")
    logger.info(f"TX Gain: {args.tx_gain} dB")
    logger.info(f"Duration: {args.duration} seconds")
    logger.info("=" * 70)
    
    # Safety countdown
    logger.warning("⚠️  RF TRANSMISSION STARTING IN 3 SECONDS")
    logger.warning("⚠️  CHECK SPEKTRUM ANALYZER NOW")
    for i in range(3, 0, -1):
        logger.warning(f"  {i}...")
        time.sleep(1)
    
    try:
        # Create flowgraph
        tb = ContinuousCarrier(
            frequency=freq_hz,
            sample_rate=2e6,
            tx_gain=args.tx_gain,
            amplitude=args.amplitude
        )
        
        # Start transmission
        tb.start()
        logger.info("=" * 70)
        logger.info("✓ TRANSMISSION ACTIVE")
        logger.info("=" * 70)
        logger.info(f"Transmitting continuous carrier at {args.frequency} MHz")
        logger.info(f"TX Gain: {args.tx_gain} dB")
        logger.info("Check your spektrum analyzer now!")
        logger.info(f"Will transmit for {args.duration} seconds...")
        logger.info("Press Ctrl+C to stop early")
        logger.info("=" * 70)
        
        # Wait for duration
        for i in range(args.duration):
            time.sleep(1)
            logger.info(f"Transmitting... {i+1}/{args.duration}s")
        
        # Stop
        tb.stop()
        tb.wait()
        
        logger.info("=" * 70)
        logger.info("✓ TRANSMISSION COMPLETED")
        logger.info("=" * 70)
        
    except KeyboardInterrupt:
        logger.warning("\nTransmission stopped by user")
        tb.stop()
        tb.wait()
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
