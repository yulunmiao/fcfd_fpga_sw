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
    kcu.write_node("SYSTEM.ETHERNET_TEST_MODE",0)
    kcu.write_node("SYSTEM.BLOCK_ACQ_MODE",1)
    kcu.write_node("SYSTEM.DESCRAMBLE_ENABLE",1)

    fifo = kcu.hw.getNode("DAQ.FIFO")

    kcu.write_node("SYSTEM.FCFD_DATA_MODE",2)
    input(f"Please set test_pattern_sel to 2.\nPress Enter to continue...") 
    logging.info(
        f"FIFO occupancy = {kcu.read_node('SYSTEM.FIFO_OCCUPANCY')}, "
        f"empty={kcu.read_node('SYSTEM.FIFO_EMPTY')}"
    )
    kcu.write_node("SYSTEM.BLOCK_ACQ_START",1)
    input()
    
    fifo_occupancy = kcu.read_node("SYSTEM.FIFO_OCCUPANCY")
    fifo = kcu.hw.getNode("DAQ.FIFO")

    # for i in tqdm(range(fifo_occupancy)):
    is_First = True
    while fifo_occupancy>0:
        try:
            fifo_output = fifo.readBlock(min(127, fifo_occupancy))
            kcu.hw.dispatch()

            if is_First:
                reference = list(fifo_output).copy()
                is_First = False

            print(fifo_output)
            for i,(e,o) in enumerate(zip(reference,fifo_output)):
                print(i,e,o,e==o)
            if reference != list(fifo_output):
                print('break')
                break
            fifo_occupancy-=127
        except (uhal.UdpTimeout):
            time.sleep(0.1)
            continue 
    # else:
    #     logging.info("Ethernet_test_mode finished with no error")
    logging.info(
        f"FIFO occupancy = {kcu.read_node('SYSTEM.FIFO_OCCUPANCY')}, "
        f"empty={kcu.read_node('SYSTEM.FIFO_EMPTY')}"
    )
