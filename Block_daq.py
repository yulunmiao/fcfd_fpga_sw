import json
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

    output_json = {}
    logging.basicConfig(level=logging.INFO)
    kcu = KCU.KCU(uhal_level="ERROR")
    test_result = {}
    kcu.write_node("SYSTEM.ETHERNET_TEST_MODE",0)
    kcu.write_node("SYSTEM.BLOCK_ACQ_MODE",1)
    kcu.write_node("SYSTEM.DESCRAMBLE_ENABLE",0)
    kcu.write_node("SYSTEM.DROP_FILLER",1)
    kcu.write_node("SYSTEM.CLEAR_UNLOCK",1)
    #kcu.write_node("SYSTEM.FCFD_DATA_MODE",0)
    fifo = kcu.hw.getNode("DAQ.FIFO")
    fifo_occupancy = kcu.read_node("SYSTEM.FIFO_OCCUPANCY")

    logging.info("Clear FIFO before test")
    # Clean FIFO entirely before test
    while fifo_occupancy>0:
        fifo.readBlock(min(255, fifo_occupancy))
        kcu.hw.dispatch()
        time.sleep(1e-4) # avoid crash
        fifo_occupancy -= 255
        
    logging.info(
        f"FIFO cleaned, occupancy={kcu.read_node('SYSTEM.FIFO_OCCUPANCY')}, "
        f"empty={kcu.read_node('SYSTEM.FIFO_EMPTY')}"
    )

    kcu.write_node("SYSTEM.FCFD_DATA_MODE",0)
    kcu.write_node("SYSTEM.DESCRAMBLE_ENABLE",1)
    kcu.write_node("SYSTEM.BLOCK_ACQ_START",1)
    try:
        while((occupancy:=kcu.read_node("SYSTEM.FIFO_OCCUPANCY"))!=256*1024):
            print(f"waiting for FIFO to fill.... occupany={occupancy}/{256*1024}")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nReadout loop terminated cleanly by user.")

    iGlobal = 0
    fifo = kcu.hw.getNode("DAQ.FIFO")

    output=[]
    fifo_occupancy = kcu.read_node("SYSTEM.FIFO_OCCUPANCY")    

    while fifo_occupancy>0:
        try:
            fifo_output = fifo.readBlock(min(127, fifo_occupancy))
            kcu.hw.dispatch()
            for i,r in enumerate(fifo_output):
                print(f"{iGlobal:>6d}:\t0x{r:08x}")
                output.append(r)
                iGlobal+=1
            fifo_occupancy-=127
        except (uhal.UdpTimeout):
            time.sleep(0.1)
            continue 

    output_json["raw_data"] = output
    with open("./test_result/test_daq.json", "w") as json_file:
        json.dump(output_json, json_file, indent=4)
    
