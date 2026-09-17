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

    # bit counter test
    kcu.write_node("SYSTEM.FCFD_DATA_MODE",3)
    input(f"Please set test_pattern_sel to 3.\nPress Enter to continue...") 

    logging.info(f"Start bit counter test")
    kcu.write_node("SYSTEM.BLOCK_ACQ_START",1)
    time.sleep(2)
    if kcu.read_node("SYSTEM.FIFO_FULL")!=1:
        logging.warning("The FIFO is not filled in fixed pattern test.")
    fifo_occupancy = kcu.read_node("SYSTEM.FIFO_OCCUPANCY")
    i=0
    while fifo_occupancy>0:
        try:
            fifo_output = fifo.readBlock(min(128, fifo_occupancy))
            kcu.hw.dispatch()
            fifo_output = np.array(fifo_output,dtype=np.uint32)
            if i == 0:
                reference = fifo_output.copy()
            condition = all([e==o for e,o in zip(reference,fifo_output)])
            if not condition:
                logging.warning(f"Mismatch found")
                logging.warning(f"expecting\treading\tdiff")
                [logging.warning(f"{e:08x}\t{o:08x}\t{o-e:08x}") for e,o in zip(expected,fifo_output)]
                break

            i+=1
            fifo_occupancy-=128
        except (uhal.UdpTimeout):
            time.sleep(0.1)
            continue 
    else:
        logging.info("Bit counter test finished with no error")
    logging.info(
        f"FIFO occupancy = {kcu.read_node('SYSTEM.FIFO_OCCUPANCY')}, "
        f"empty={kcu.read_node('SYSTEM.FIFO_EMPTY')}"
    )
    