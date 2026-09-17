from typing import List, Dict
import pprint


class FCFD_unpacker():

    HEADER_FIELDS = {
        "header_delimiter": {"value": 0x8b, "shift": 24, "mask": 0xff},
        "type": {"shift": 23, "mask": 0x1},
        "groupid": {"shift": 20, "mask": 0x7},
        "upper_bxid": {"shift": 9, "mask": 0x7ff},
        "bxid": {"shift": 0, "mask": 0x1ff},
    }

    TDC_FIELDS = {
        0:{
            0:{
                "ERR_CODE":{"shift": 28,"mask": 0x7},
                "CH_ID":{"shift":24,"mask":0xf},
                "CLK_TAG":{"shift":21,"mask":0x7},
                "ADC":{"shift":16,"mask":0x1f},
                "TOA0":{"shift":8,"mask":0xff},
                "CAL0":{"shift":0,"mask":0xff}
            },
            1:{
                "CAL_SUM":{"shift":16,"mask":0x7fff,"signed":True},
                "TOA_SUM":{"shift":0,"mask":0xffff,"signed":True}
            }
        },
        1:{
            0:{
                "ERR_CODE":{"shift": 28,"mask": 0x7},
                "CH_ID":{"shift":24,"mask":0xf},
                "CLK_TAG":{"shift":21,"mask":0x7},
                "ADC":{"shift":16,"mask":0x1f},
                "TOA0":{"shift":8,"mask":0xff},
                "CAL0":{"shift":0,"mask":0xff}
            },
            1: {
                "dCAL1":{"shift": 24,"mask": 0xf},
                "dCAL2":{"shift": 20,"mask": 0xf},
                "dCAL3":{"shift": 16,"mask": 0xf},
                "dCAL4":{"shift": 12,"mask": 0xf},
                "dCAL5":{"shift": 8,"mask": 0xf},
                "dCAL6":{"shift": 4,"mask": 0xf},
                "dCAL7":{"shift": 0,"mask": 0xf},
            }
        }
    }

    TRAILER_FIELDS = {
        "trailer_delimiter": {"value": 0x8d, "shift": 24, "mask": 0xff},
        "status": {"shift":8,"mask":0xffff},
        "crc": {"shift":0,"mask":0xff}
    }


    def __init__(self, config: dict):
        self._config = config

    def _get_bits(self, value: int, field: Dict[str, int]) -> int:
        result = (value >> field["shift"]) & field["mask"]
        if field.get("signed") and result & (field["mask"] + 1) >> 1:
            result -= field["mask"] + 1
        return result

    def parse_to_dataframes(self, raw: List[int])->List[List[int]]:
        packages = []
        package = []
        in_package = False
        header_field = self.HEADER_FIELDS["header_delimiter"]
        trailer_field = self.TRAILER_FIELDS["trailer_delimiter"]
        get_bits = self._get_bits

        for word in raw:
            if not in_package:
                if get_bits(word, header_field) != header_field["value"]:
                    continue
                package = [word]
                in_package = True
            else:
                if get_bits(word, header_field) == header_field["value"]:
                    raise ValueError("Find package header inside a package")
                package.append(word)

            if get_bits(word, trailer_field) == trailer_field["value"]:
                packages.append(package)
                package = []
                in_package = False
        return packages

    def parse_dataframe(self, dataframe: List[int]) -> Dict:
        data = {}
        for field in ["type","groupid","upper_bxid","bxid"]:
            data[field] = self._get_bits(dataframe[0], self.HEADER_FIELDS[field])
        tdc_field = self.TDC_FIELDS[self._config["tdc_encoder"]]
        tdc_dataframes = dataframe[1:-1]

        if len(tdc_dataframes) % 2 != 0:
            raise ValueError("TDC data must contain two words per measurement") 

        data["tdc"] = []
        for index in range(0, len(tdc_dataframes), 2):
            tdc_data = {}
            for word_index, word in enumerate(tdc_dataframes[index:index + 2]):
                for field, definition in tdc_field[word_index].items():
                    tdc_data[field] = self._get_bits(word, definition)
            data["tdc"].append(tdc_data)

        for field in ["status","crc"]:
            data[field] = self._get_bits(dataframe[1], self.TRAILER_FIELDS[field])
        return data


def main():
    config = {}
    config["tdc_encoder"]=0
    unpacker = FCFD_unpacker(config)
    import json
    with open("./test_result/test_time_scan_10.00001MHz_TDC0.json", "r") as json_file:
        data = json.load(json_file)["raw_data"]
    packages =  unpacker.parse_to_dataframes(data)
    for i,p in enumerate(packages):
        print(f"parsed package {i}:")
        for ii,w in enumerate(p):
            print(f"{ii}:0x{w:08x}")
        parsed = unpacker.parse_dataframe(p)
        print("package parsed result is")
        pprint.pp(parsed)


if __name__ == "__main__":
    main()