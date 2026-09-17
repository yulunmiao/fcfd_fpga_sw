import utils.KCU as KCU
import json
import time
if __name__ == "__main__":
    kcu = KCU.KCU(uhal_level="ERROR")
    test_result = {}
    for i in range(8):
        input(f"Please set ser_drive_str to {i}.\nPress Enter to continue...") 
        kcu.write_node("SYSTEM.ALIGNER_AUTO_MODE",1)
        kcu.write_node("SYSTEM.ALIGNER_START_TEST",1)

        while(True):
            time.sleep(0.1)
            test_done = kcu.read_node("SYSTEM.ALIGNER_TEST_DONE")
            if test_done == 1:
                break
        fail = kcu.read_node("SYSTEM.ALIGNER_FAIL")
        error_flag = kcu.read_node("SYSTEM.ALIGNER_ERROR_FLAG")
        scan_tables = []
        for ii in range(16):
            scan_table = kcu.read_node(f"SYSTEM.SCAN_TABLE_{ii}")
            scan_tables.append(scan_table)
        test_result[i] = {
            "Fail Flag": fail,
            "Error Flag": error_flag,
            "Scan Tables": scan_tables
        }
    with open("./test_result/test_bit_aligner.json", "w") as json_file:
        json.dump(test_result, json_file, indent=4)