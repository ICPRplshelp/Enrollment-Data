"""Script that compiles drop rates for all courses, with the sections specified
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Callable

from importable_scripts import cinterfaces


def get_drop_date(fsy: str, constants_json: dict[str, int]) -> int:
    """"""
    fsy = fsy.upper()
    if fsy == 'F':
        return constants_json['fallDrop']
    elif fsy == 'S':
        return constants_json['winterDrop']  # 1674446400
    else:
        return constants_json['yearDrop']


def find_first_index(li: list[int], predicate: Callable[[int], bool]) -> int:
    """Return the first index in li that satisfies the predicate, or
    -1 if none do"""
    for i, x in enumerate(li):
        if predicate(x):
            return i
    return -1


def get_cutoff_date(fsy: str, constants_json: dict[str, int]) -> int:
    """"""
    # print(constants_json)
    if fsy == 'F':
        return constants_json['fallEnrollmentEnd']
    elif fsy == 'S':
        return constants_json['winterEnrollmentEnd']
    else:
        return constants_json['fallEnrollmentEnd']


@dataclass
class CourseInfo:
    code: str
    enroll_cutoff: int
    cap: int
    drops: int  # does not contain lwds
    lwd: int
    faculty: str
    cur_enrollment: int

    def get_total_drops(self) -> int:
        return self.drops + self.lwd

    def merge_other(self, other: CourseInfo) -> None:
        self.enroll_cutoff += other.enroll_cutoff
        self.cap += other.cap
        self.drops += other.drops
        self.lwd += other.lwd
        self.cur_enrollment += other.cur_enrollment

    def get_code_only(self) -> str:
        return self.code[:8]

    def __str__(self) -> str:
        return f'{self.code} | D: {100 * self.calc_drop_rate():.2f}% | LWD: {100 * self.calc_lwd_rate():.2f}%'

    def calc_drop_rate(self) -> float:
        if self.enroll_cutoff != 0:
            return max(self.drops / self.enroll_cutoff, 0)
        else:
            return 0

    def calc_lwd_rate(self) -> float:
        if self.enroll_cutoff != 0:
            return max(self.lwd / self.enroll_cutoff, 0)
        else:
            return 0

    def calc_total_drop_rate(self) -> float:
        """Calculate the total drop rate, which is drops + lwds combined.
        Cannot exceed 1"""
        return min(1.0, self.calc_drop_rate() + self.calc_lwd_rate())


class BulkCourseInfo(CourseInfo):
    pass


def get_specific_constants_object(course_code: str, faculty: str, combined_crs_dict: list[dict]) -> dict:
    current_object = None
    for item in combined_crs_dict:
        if item['faculty'] == faculty:
            current_object = item
            break

    if current_object is None:
        # CSC110Y1F
        campus_code = course_code[7]
        if campus_code == '3' and 'SCAR' in [x['faculty'] for x in combined_crs_dict]:
            current_object = next(x for x in combined_crs_dict if x['faculty'] == 'SCAR')
        else:
            current_object = next(x for x in combined_crs_dict if x['faculty'] == 'ARTSC')

    # current_object should be the one that is returned
    return current_object['importantTimestamps']


def main(path_to_session_folder: str) -> list[CourseInfo]:
    """For every course, compile their drop rate and all other information."""
    path_to_session_folder = path_to_session_folder.removesuffix('/').removesuffix('\\')
    with open(f"{path_to_session_folder}/AAtcconstants.json", encoding="UTF-8") as f:
        constants_data_totaled = json.load(f)

    rg = re.compile(r'[A-Z]{3}([A-D]|\d)\d{2}[HY]\d[FSY].json')
    li = os.listdir(path_to_session_folder)
    accum = []
    li = [x for x in li if rg.match(x)]
    for course_dir in li:
        with open(os.path.join(path_to_session_folder, course_dir), encoding='UTF-8') as f:
            data: cinterfaces.Course = json.load(f)
        constants_data = get_specific_constants_object(data['code'], data['faculty'], constants_data_totaled)
        meetings_list = data['meetings']

        fsy = data['code'][-1]
        timelogs = data['timeIntervals']
        m_array = [x['enrollmentLogs'] for x in meetings_list]
        # transpose the list above
        m_array = [list(x) for x in zip(*m_array)]
        m_total = [sum(x) for x in m_array]
        # and now we have a list of all enrollments
        cutoff_date = get_cutoff_date(fsy, constants_data) + 70000  # cutoff date pushed back a bit
        drop_date = get_drop_date(fsy, constants_data)
        # if data['faculty'] == 'SCAR':
        #     drop_date = get_drop_date_utsc(fsy)

        if len(m_total) == 0 or -1 in m_total:
            print(f"continuing on {data['code']}")
            continue
        try:
            cutoff_enrol = m_total[min(find_first_index(timelogs, lambda s: s > cutoff_date), len(m_total) - 1)]
            drop_date_enrol = m_total[
                min(find_first_index(timelogs, lambda s: s > drop_date + 160000), len(m_total) - 1)]
            lwd_enrol = m_total[-1]
        except IndexError:
            print(f"continuing on {data['code']}")
            continue
        drops = cutoff_enrol - drop_date_enrol
        lwds = drop_date_enrol - m_total[-1]
        drop_rate = drops / max(cutoff_enrol, 1)
        lwd_rate = lwds / max(cutoff_enrol, 1)
        # print(f"{data['code']} has {drops} drops")
        t_cap = sum(x['enrollmentCap'] for x in meetings_list)
        c_i = CourseInfo(data['code'], cutoff_enrol, t_cap, drops, lwds, data['faculty'], lwd_enrol)
        accum.append(c_i)
    return accum


def main2(accum_main: list[CourseInfo]) -> list[tuple[str, dict[str, int]]]:
    t_dict = {}
    for item in accum_main:
        crs_code = item.get_code_only()
        if crs_code not in t_dict:
            t_dict[crs_code] = item
        else:
            t_dict[crs_code].merge_other(item)

    ######
    new_dict = [(x, {"d": max(y.get_total_drops(), 0), "o": max(y.enroll_cutoff, 0)}) for x, y in t_dict.items() if
                y.enroll_cutoff > 0]
    return new_dict


def generate_drop_rates(ses_code: str) -> None:
    create_folder_if_not_exists("../aggregated_jsons")
    m_tmp = main("../" + ses_code)
    m_tmp_2 = main2(m_tmp)
    m_tmp_3 = {"session": ses_code, "dMap": m_tmp_2}
    with open(f"../aggregated_jsons/{ses_code}_totals.json", "w", encoding="UTF-8") as f:
        json.dump(m_tmp_3, f, separators=(",", ":"))


def create_folder_if_not_exists(folder_path: str) -> None:
    if not os.path.exists(folder_path):
        try:
            os.makedirs(folder_path)
        except OSError as e:
            print(f"Error creating folder '{folder_path}': {e}")


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        generate_drop_rates("20239")
    else:
        generate_drop_rates(sys.argv[1])
