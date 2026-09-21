from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import utils.KCU as KCU
import matplotlib.pyplot as plt
import time
import logging
import numpy as np
import uhal
from tqdm import tqdm
from typing import Iterator

if __name__ == "__main__":
    # overflow is intendedly used for counter, thus turning off the warning
    np.seterr(over='ignore')
    
    logging.basicConfig(level=logging.INFO)
    kcu = KCU.KCU(uhal_level="ERROR")
    test_result = {}

    # Use block acquisition
    kcu.write_node("SYSTEM.BLOCK_ACQ_MODE",1)
    kcu.write_node("SYSTEM.DESCRAMBLE_ENABLE",1)

    fifo = kcu.hw.getNode("DAQ.FIFO")
    # Clean FIFO entirely before test
    logging.info("Clear FIFO before test")
    fifo_occupancy = kcu.read_node("SYSTEM.FIFO_OCCUPANCY")
    while fifo_occupancy>0:
        fifo.readBlock(min(255, fifo_occupancy))
        kcu.hw.dispatch()
        time.sleep(1e-4) # avoid crash
        fifo_occupancy -= 255
        
    logging.info(
        f"FIFO cleaned, occupancy={kcu.read_node('SYSTEM.FIFO_OCCUPANCY')}, "
        f"empty={kcu.read_node('SYSTEM.FIFO_EMPTY')}"
    )

    # Fixed Pattern test
    kcu.write_node("SYSTEM.ETHERNET_TEST_MODE",0)
    kcu.write_node("SYSTEM.FCFD_DATA_MODE",2)
    input(f"Please set test_pattern_sel to 2.\nPress Enter to continue...") 

    logging.info(f"Start fixed pattern test")
    kcu.write_node("SYSTEM.BLOCK_ACQ_START",1)
    time.sleep(2)
    if kcu.read_node("SYSTEM.FIFO_FULL")!=1:
        logging.warning("The FIFO is not filled in fixed pattern test.")
    # N.B. there is a know problem that the first 5 words can become from previous setting, skip them.
    # _ = fifo.readBlock(5)
    fifo_occupancy = kcu.read_node("SYSTEM.FIFO_OCCUPANCY")
    while fifo_occupancy>0:
        try:
            fifo_output = fifo.readBlock(min(255, fifo_occupancy))
            kcu.hw.dispatch()

            condition = all([o ==0x5c5c5c5c  for o in fifo_output])
            if not condition:
                print("Alea iacta ")
                logging.warning(f"Mismatch found")
                logging.warning(f"expecting\treading\tdiff")
                [logging.warning(f"{0x5c5c5c5c}\t{o}\t{o-e}") for o in fifo_output]
                break
            fifo_occupancy-=255
        except (uhal.UdpTimeout):
            time.sleep(0.1)
            continue 
    else:
        logging.info("Fixed pattern test finished with no error")
    logging.info(
        f"FIFO occupancy = {kcu.read_node('SYSTEM.FIFO_OCCUPANCY')}, "
        f"empty={kcu.read_node('SYSTEM.FIFO_EMPTY')}"
    )
