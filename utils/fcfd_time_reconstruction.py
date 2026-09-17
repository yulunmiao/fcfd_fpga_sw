import numpy as np
from utils.fcfd_unpacker import FCFD_unpacker

import matplotlib.pyplot as plt
import mplhep as hep
plt.style.use([hep.style.ROOT, hep.style.firamath])

def time_reconstruction(clk_tag: int,n:int, cal0:int, cal_sum:int, toa0:int, toa_sum:int):
    # return reconstructed time in ps
    T_320 = 3125
    w = np.floor(n**2/4)
    m_triangle = cal0+cal_sum/w
    deltat_fine = T_320/m_triangle
    C_fine = toa0+toa_sum/n+cal0*(n-1)/2+0.5
    t_fine = C_fine * deltat_fine
    t_shift = (n-1)/2*T_320
    t_hit = clk_tag * T_320 + t_fine - t_shift
    return t_hit


if __name__ == "__main__":
    config = {}
    config["tdc_encoder"]=0
    unpacker = FCFD_unpacker(config)
    import json
    with open("./test_result/test_time_scan_10.00001MHz_TDC0.json", "r") as json_file:
        data = json.load(json_file)["raw_data"]
    packages =  unpacker.parse_to_dataframes(data)
    for i,p in enumerate(packages):
        parsed = unpacker.parse_dataframe(p)
        tdc = parsed['tdc'][0]
        t = time_reconstruction(tdc['CLK_TAG'],8,tdc['CAL0'],tdc['CAL_SUM'],tdc['TOA0'],tdc['TOA_SUM'])
        print(i,t)