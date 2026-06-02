"""Run this to add autocomplete stuff
RUN:
python generate_autocomplete.py <SESSION>
example for session: 20239 for fall-winter 2023
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass


@dataclass
class Designator:
    des: str
    courses: list[Course]

    def export_dict(self) -> dict:
        return {
            'des': self.des,
            'courses': [x.export_dict() for x in self.courses]
        }


@dataclass
class Course:
    num: str
    cvr: list[CVariant]

    def export_dict(self) -> dict:
        return {'n': self.num, 'v': [x.export_dict() for x in self.cvr]}


@dataclass
class CVariant:
    cmp: str  # 0, 1, 3, 5, 9, or blank
    wt: str  # H or Y
    ses: str  # F/S/Y with a number at the end

    def export_dict(self) -> dict[str, str]:
        return {
            'c': self.cmp,
            'w': self.wt,
            's': self.ses
        }


def c_variant_key(item: CVariant) -> tuple[str, str, str]:
    # campus asc, wt asc, then ses asc
    t1 = item.cmp
    t2 = item.wt
    t3 = item.ses
    return t1, t2, t3


def get_all_des(session: str) -> list[Designator]:
    c_li = get_all_course_codes(session)
    dl = generate_des_list(c_li)
    # print(dl)
    return dl


def get_all_course_codes(ses: str) -> list[str]:
    """Get all file names from the specified section"""
    c_list_folder = os.listdir("../"+ ses)
    c_list_2 = [x.removesuffix(".json") for x in c_list_folder if x.endswith(".json")]
    return c_list_2


def generate_des_list(li: list[str]) -> list[Designator]:
    # only courses matching this specific regex can be accounted for
    rg_p = re.compile(r'^[A-Z]{3}[A-D\d]\d{2}[HY][0135][FSY]$')
    li2 = []
    for x in li:
        if rg_p.match(x):
            li2.append(x)
        else:
            print(f'did not match {x}')
    # courses
    crs_dict: dict[str, list[CVariant]] = {}
    for cr in li2:
        # loop precond: li2 looks like a
        # course code with a dash
        full_code = cr[:6]
        # des = cr[:3]
        # c_num = cr[3:6]
        wt = cr[6]
        cmp = cr[7]
        ses = cr[8]
        # CSC110Y1F
        cvr_temp = CVariant(cmp, wt, ses)
        if full_code not in crs_dict:
            crs_dict[full_code] = []
        crs_dict[full_code].append(cvr_temp)
    # loop postconditions:
    # crs dict's key is every AAA100 course code
    course_list: list[Course] = []

    for cr_c, lcv in crs_dict.items():
        lcv.sort(key=c_variant_key)
        t_c = Course(cr_c, lcv)
        course_list.append(t_c)

    # loop post conditions: course_list is a list
    # of every course.

    # loop post conditions
    # I want a dict of {CSC: list[Courses]}

    temp_des_dict: dict[str, list[Course]] = {}

    for cr_t2 in course_list:
        ct = cr_t2.num[:3]  # ct is the des
        # and matches the regex [A-Z]{3}
        if ct not in temp_des_dict:
            temp_des_dict[ct] = []
        temp_des_dict[ct].append(cr_t2)

    # post conditions are met by then
    dt_list: list[Designator] = []
    for dt, dti in temp_des_dict.items():
        desig = Designator(dt, dti)
        dt_list.append(desig)

    return dt_list


def export_json(dict_to_json: dict, file_name: str) -> None:
    j_data = json.dumps(dict_to_json, indent=None, separators=(',', ':'))
    with open(file_name, 'w') as f:
        f.write(j_data)


LD = {
    'A': '1', 'B': '2', 'C': '3', 'D': '4'
}


def utsc_flattener(crs_code: str) -> str:
    """I HATE FILE EXPANDERS"""
    return crs_code[:3] + LD.get(crs_code[3], crs_code[3]) + crs_code[4:]


def main(ses: str) -> None:
    tm = get_all_des(ses)
    export_json({'liDes': [x.export_dict() for x in tm]}, f'../{ses}/AAclistall.json')


if __name__ == '__main__':
    # DOES NOT MAKE ANY CONTACT WITH THE INTERNET FOR ANY REASON.
    import sys
    if len(sys.argv) < 2:
        main('20249')
    else:
        main(sys.argv[1])
