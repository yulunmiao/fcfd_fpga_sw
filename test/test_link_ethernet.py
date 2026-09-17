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

    # Test with ethernet_test_mode
    logging.info("Running with ethernet_test_mode")
    kcu.write_node("SYSTEM.ETHERNET_TEST_MODE",1)
    kcu.write_node("SYSTEM.BLOCK_ACQ_START",1)
    time.sleep(2)
    input()
    if kcu.read_node("SYSTEM.FIFO_FULL")!=1:
        logging.warning("The FIFO is not filled in ethernet_test_mode test.")    # Try switch to next test before read out fifo
    fifo_occupancy = kcu.read_node("SYSTEM.FIFO_OCCUPANCY")
    # 20-bit counter used in this test
    i = 0
    mask = (1 << 20) - 1  
    while fifo_occupancy>0:
        try:
            fifo_output = fifo.readBlock(min(255, fifo_occupancy))
            kcu.hw.dispatch()
            fifo_output = np.array(fifo_output,dtype=np.uint32)
            if i == 0:
                reference = fifo_output.copy()

            expected = [(_+i*255) & mask for _ in reference]

            condition = all([e==o for e,o in zip(expected,fifo_output)])
            if not condition:
                logging.warning(f"Mismatch found")
                logging.warning(f"expecting\treading\tdiff")
                [logging.warning(f"{e}\t{o}\t{o-e}") for e,o in zip(expected,fifo_output)]
                break

            i+=1
            fifo_occupancy-=255
        except (uhal.UdpTimeout):
            time.sleep(0.1)
            continue 
    else:
        logging.info("Ethernet_test_mode finished with no error")
    logging.info(
        f"FIFO occupancy = {kcu.read_node('SYSTEM.FIFO_OCCUPANCY')}, "
        f"empty={kcu.read_node('SYSTEM.FIFO_EMPTY')}"
    )
