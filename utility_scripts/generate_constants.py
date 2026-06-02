"""
RUN:
python generate_constants.py <SESSION>
example for session: 20239 for fall-winter 2023
"""


from pathlib import Path
from typing import Union
import json
import sys


def convert_tsv_to_list(tsv_string: str) -> list[list[str]]:
    lines = tsv_string.strip().splitlines()[1:]
    d_list = []
    for line in lines:
        row = line.split("\t")
        d_list.append(row)
    return d_list


def narrow_to_bool_int(val: str) -> Union[int, bool, None]:
    if val == "":
        return None
    if val.lower() == "false":
        return False
    if val.lower() == "true":
        return True
    return int(val)


def create_json_from_crs_block(dl: list[list[str]]) -> dict[str, Union[int, bool, None]]:
    c_dict = {}
    for elem in dl:
        nb = narrow_to_bool_int(elem[1]) if len(elem) > 1 else None
        c_dict[elem[0]] = nb
    return c_dict


def generate_info(fp: str) -> list[dict]:
    """Produces the output JSON from the given file path"""
    contents = Path("inputcsv.csv").read_text()
    as_list = convert_tsv_to_list(contents)

    utsg = [x[0:2] for x in as_list]
    utsc = [x[2:4] for x in as_list]
    utm = [x[4:6] for x in as_list]

    utsg_json = create_json_from_crs_block(utsg)
    utsc_json = create_json_from_crs_block(utsc)
    utm_json = create_json_from_crs_block(utm)

    final_lst = []
    for json_info, faculty in zip([utsg_json, utsc_json, utm_json], ["ARTSC", "SCAR", "ERIN"]):
        final_lst.append({
            "faculty": faculty,
            "importantTimestamps": json_info
        })
    return final_lst


def prog_with_args(c_session: str) -> None:
    gen_info = generate_info("inputcsv.csv")
    # print(gen_info)
    with open(f"../{c_session}/AAtcconstants.json", "w", encoding="UTF-8") as f:
        json.dump(gen_info, f, indent=2)

def prog():
    """
    UTMImportantDates sheet,
    F:K 1:28
    Goes into inputcsv
    """
    if len(sys.argv) != 2:
        print("You must specify the session no. in the first argument")
        return
    c_session = sys.argv[1]
    prog_with_args(c_session)


if __name__ == '__main__':
    prog()
