import utils.KCU as KCU
import matplotlib.pyplot as plt
import time


if __name__ == "__main__":
    kcu = KCU.KCU(uhal_level="ERROR")
    kcu.uhal.disableLogging()
    values = []
    fifo = kcu.hw.getNode("DAQ.FIFO")

    error_words = []

    for ii in range(100):
        repeats = ii
        start_time = time.perf_counter()
        for i in range(repeats):
            # try: 
            for _ in range(i):
                block_data = fifo.readBlock(255)
                kcu.hw.dispatch()
            # except Exception as e:
            #     print(f"Error encoutered while reading {i} words simultaneously: {e}")
            #     error_words.append(i)
            #     print(f"{ii}:{i}words")
            #     break
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        speed = repeats*255/elapsed_time
        print(f"{ii}: {start_time}, {end_time} speed = {speed*32/1e6} Mbps")
    #plt.hist(error_words,10)
    #plt.show()
    # for i in range(16384):
    #     value = kcu.read_node(f"DAQ.FIFO", dispatch=False)
    #     values.append(value)
    # kcu.dispatch()
    # print("FIFO read values:")
    # for i, value in enumerate(values):
    #     print(f"0x{i:02x}({i}) = 0x{value:08x} ({value}), diff: {value - i}")
