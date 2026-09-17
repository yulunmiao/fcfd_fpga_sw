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

    print("Please ensure the following set ups:")
    #print("channel_mask = 0b0 (0)")
    print("channel_mask = 0b111110 (62)")
    print("tdc_ext_test = 0b0 (0)")
    print("tdc_test_hit_freq = 0b11 (3)")
    input("Press enter to continue...")


    kcu.write_node("SYSTEM.FCFD_DATA_MODE",0)
    kcu.write_node("SYSTEM.DESCRAMBLE_ENABLE",1)
    for i in [4,8,16,32]:
        print(f"Set tdc_timestamp_num = {i}")
        input("Press enter to continue...")
        kcu.write_node("SYSTEM.BLOCK_ACQ_START",1)
        time.sleep(2)
        input()
        iGlobal = 0
        fifo = kcu.hw.getNode("DAQ.FIFO")
        output=[]
        fifo_occupancy = kcu.read_node("SYSTEM.FIFO_OCCUPANCY")

        while fifo_occupancy>0:
            try:
                fifo_output = fifo.readBlock(min(255, fifo_occupancy))
                kcu.hw.dispatch()
                for _ in fifo_output:
                    output.append(_)
                    print(f"{iGlobal:>6d}:0x{_:08x}")
                    iGlobal+=1
                fifo_occupancy-=255
            except (uhal.UdpTimeout):
                time.sleep(0.1)
                continue 
        output_json[i]=output
    with open("./test_result/test_time_internal.json", "w") as json_file:
        json.dump(output_json, json_file, indent=4)
    