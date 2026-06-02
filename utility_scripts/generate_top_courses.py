"""
{
  "start": 1656907200,
  "fourth": 1657512000,
  "third": 1657771200,
  "second": 1658116800,
  "first": 1658376000,
  "general": 1659067200,
  "utmutsc": 1659693600,
  "feeDeadline": 1661918400,
  "fallFirstDay": 1662609600,
  "fallWaitlistClosed": 1663387200,
  "fallEnrollmentEnd": 1663819200,
  "fallDrop": 1668571200,
  "fallLWD": 1670385600,
  "winterStart": 1673236800,
  "winterWaitlistClosed": 1674187200,
  "winterEnrollmentEnd": 1674446400,
  "yearDrop": 1676952000,
  "winterDrop": 1679284800,
  "winterLWD": 1680753600,
  "endOfYear": 1682740800
}
"""
from typing import Callable
import csv


def get_drop_date(fsy: str, constants_json: dict[str, int]) -> int:
    """"""
    constants_json = constants_json[0]["importantTimestamps"]
    fsy = fsy.upper()
    if fsy == 'F':
        return constants_json['fallDrop']
    elif fsy == 'S':
        return constants_json['winterDrop']  # 1674446400
    else:
        return constants_json['yearDrop']


def get_drop_date_utsc(fsy: str, constants_json: dict[str, int]) -> int:
    fsy = fsy.upper()
    if fsy == 'F':
        return constants_json['fallDrop'] + 270000  # overshoot-type estimation
    elif fsy == 'S':
        return constants_json['fallDrop'] + 270000
    else:
        return constants_json['fallDrop'] + 270000


def get_cutoff_date(fsy: str, constants_json: dict[str, int]) -> int:
    """"""
    constants_json = constants_json[0]["importantTimestamps"]
    if fsy == 'F':
        return constants_json['fallEnrollmentEnd']
    elif fsy == 'S':
        return constants_json['winterEnrollmentEnd']
    else:
        return constants_json['fallEnrollmentEnd']


import re
from dataclasses import dataclass
import os
import json


@dataclass
class CourseInfo:
    code: str
    enroll_cutoff: int
    cap: int
    drops: int  # does not contain lwds
    lwd: int
    faculty: str
    cur_enrollment: int

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

    def export_csv_row(self) -> list[str]:
        return [self.code, self.cur_enrollment, str(self.enroll_cutoff), str(self.cap), str(self.drops), str(self.lwd),
                str(self.calc_drop_rate()), str(self.calc_lwd_rate()), str(self.calc_total_drop_rate())]


def find_first_index(li: list[int], predicate: Callable[[int], bool]) -> int:
    """Return the first index in li that satisfies the predicate, or
    -1 if none do"""
    for i, x in enumerate(li):
        if predicate(x):
            return i
    return -1


def main(path_to_session_folder: str) -> list[CourseInfo]:
    """For every course, compile their drop rate and all other information."""
    path_to_session_folder = path_to_session_folder.removesuffix('/').removesuffix('\\')
    with open(f"../{path_to_session_folder}/AAtcconstants.json", encoding="UTF-8") as f:
        constants_data = json.load(f)
    rg = re.compile(r'[A-Z]{3}([A-D]|\d)\d{2}[HY]\d[FSY].json')
    li = os.listdir(os.path.join("..", path_to_session_folder))
    accum = []
    li = [x for x in li if rg.match(x)]
    for course_dir in li:
        with open(f'../{path_to_session_folder}/{course_dir}', encoding='UTF-8') as f:
            data = json.load(f)
        meetings_list = data['meetings']

        fsy = data['code'][-1]
        timelogs = data['timeIntervals']
        m_array = [x['enrollmentLogs'] for x in meetings_list]
        # transpose the list above
        m_array = [list(x) for x in zip(*m_array)]
        m_total = [sum(x) for x in m_array]
        # and now we have a list of all enrollments
        cutoff_date = get_cutoff_date(fsy, constants_data)
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
        lwds = drop_date_enrol - lwd_enrol
        drop_rate = drops / max(cutoff_enrol, 1)
        lwd_rate = lwds / max(cutoff_enrol, 1)
        # print(f"{data['code']} has {drops} drops")
        t_cap = sum(x['enrollmentCap'] for x in meetings_list)
        c_i = CourseInfo(data['code'], cutoff_enrol, t_cap, drops, lwds, data['faculty'], lwd_enrol)
        accum.append(c_i)
    return accum


def main_generate_csv() -> None:
    tv = main("../20229")  # replace this with the path to the session folder that contains all the courses
    tv.sort(key=lambda s: (s.calc_total_drop_rate(), s.drops), reverse=True)
    csv_stuff = [x.export_csv_row() for x in tv]
    os.remove('../ignored_files/output.csv')
    with open('../ignored_files/output.csv', 'w', encoding='UTF-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['code', 'cur_enrollment', 'enroll_at_cutoff', 'cap', 'drops', 'lwds', 'drop_rate', 'lwd_rate',
                         'total_drop_rate'])
        writer.writerows(csv_stuff)


def main_generate_fav_courses() -> None:
    tv = main("../20229")
    tv.sort(key=lambda s: s.enroll_cutoff)
    print(tv)


def generate_fav_courses(sessions: list[str]) -> None:
    """Generates JSON files of fav courses and"""
    for ses in sessions:
        crs_listings = generate_fav_courses_session(ses)[:120]
        j_dict = {"courses": crs_listings}
        print(j_dict)
        with open(f"../{ses}/aaTopCourses.json", "w", encoding="UTF-8") as f:
            json.dump(j_dict, f)


def course_sort_key(crs: CourseInfo) -> int:
    capacity = crs.cap
    if capacity > 3950:
        capacity = 10
    return capacity


def generate_fav_courses_session(session: str) -> list[str]:
    tv = main(f"{session}")
    tv.sort(key=course_sort_key, reverse=True)
    return [x.code for x in tv if x.faculty == "ARTSC" or (x.faculty == "UNKNOWN" and x.code[7] == '1')]


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        generate_fav_courses(["20249"])
    else:
        generate_fav_courses(sys.argv[1:])
    # main_generate_fav_courses()
    # main_generate_csv()
