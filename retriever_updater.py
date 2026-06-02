"""This module is responsible for updating all the API files. It may not
send a push."""

from __future__ import annotations

import json
import logging
import math
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Union, Optional

from importable_scripts import cinterfaces as ci
from importable_scripts import timetable_retriever as jsonviewer

DEBUG_MODE = False  # when this is true, prevent saving.
TIME_RIGHT_NOW = time.time()
FORBIDDEN = [x.strip() for x in jsonviewer.open_file("unwanted_codes.txt", True).split(",")] if os.path.exists("unwanted_codes.txt") else []


def run_this(sessions: Union[list[str], None], session_name: str, fall_over: bool) -> list[Course]:
    """Checkpoint: this works
    Updates all courses and returns their information
    Return value does not need to be used
    """
    create_folder_if_not_exists(session_name)
    tmp = create_and_update_all_courses(sessions, session_name, fall_over)
    if not DEBUG_MODE:
        export_all_courses(tmp, session_name)
    return tmp


def create_and_update_all_courses(sessions: Union[list[str], None], session_name: str, fall_over: bool = False) -> list[
    Course]:
    """Run and updates all courses.
    Return a list of courses such that all of them can be exported.
    """
    if sessions is None:
        print("Did you NOT state a session?")
        exit()
    print("Attempting to scrap the timetable...")
    t_start = time.perf_counter()
    # whatever this is, is the ttb response in JSON format.
    ttb_response = jsonviewer.get_stuff_2(sessions)
    print("Scrapped the timetable.")
    t_end = time.perf_counter()
    print(f"Scrapping the timetable took {abs(t_end - t_start):.2f} seconds.")

    c_list, c_dict = grab_all_course_jsons(session_name, fall_over)

    course_map = get_all_existing_course_objects(c_dict)
    new_course_map: dict[str, Course] = {}
    # grab all course codes from ttb_response
    constants_data = None
    # with open(f'{session_name}/AAtcconstants.json', 'r', encoding='UTF-8') as f:
    #     constants_data = json.load(f)
    all_course_info = grab_all_codes_from_response(ttb_response)
    for crs_info in all_course_info:
        course_code = crs_info["code"]
        course_offering_code = course_code + crs_info["sectionCode"]

        # construct the corresponding course info (Course)
        corresponding_course_info: Course = course_map.get(course_offering_code, None)
        if corresponding_course_info is None:
            corresponding_course_info = create_new_course(course_offering_code, crs_info["name"])
            new_course_map[course_offering_code] = corresponding_course_info
        # judge_time = s_final_enroll if crs_info['sectionCode'] == 'F' else year_end_time
        # if math.floor(time.time()) <= judge_time:  # if the current time
        # is earlier than the judgement time
        corresponding_course_info.update_all_meetings(crs_info, constants_data)
    course_map.update(new_course_map)
    print('packaged data to export')
    return [course_map[x] for x in course_map]


def export_all_courses(crs_list: list[Course], session_name: str) -> None:
    """Exports all course information to the folder 20229

    session_name is the name of the folder to 20229 to. it must not
    contain any slashes.
    """
    assert '/' not in session_name
    assert '\\' not in session_name
    print("attempting to export JSONs")
    for crs in crs_list:
        crs_code = crs.code
        file_name = crs_code + ".json"
        if crs.no_course_info():
            logging.warning(f"This course {crs.code} doesn't have any meetings")
            continue

        json_contents = json.dumps(crs.export(), indent=0, sort_keys=True)
        jsonviewer.write_file(json_contents, f"{session_name}/{file_name}")  # print(f"exported export2/{file_name}")
    print('JSON export complete')


def get_all_existing_course_objects(to_input: dict) -> dict[str, Course]:
    return {code: construct_existing_course(info) for code, info in to_input.items()}


def grab_all_codes_from_response(data: dict) -> list[dict]:
    """Grab the list of courses from the ttb response."""
    return data["courses"]


def grab_all_course_jsons(session_name: str, disallow_f: bool = False) -> tuple[list[dict], dict[dict]]:
    """Grab everything from 20229, put it into a list,
    and return it. The dict is raw.
    For dict, each course code (e.g. MAT135H1-F) is mapped to its
    respective info.
    """
    assert '/' not in session_name and '\\' not in session_name
    all_files = os.listdir(session_name)
    list_of_dicts: list[dict] = []
    dict_of_dicts: dict[dict] = {}
    if not disallow_f:
        pattern = re.compile(r"^[A-Z]{3}([A-D]|\d)\d{2,3}[HY]\d?[FSY]\d?.json$")
    else:  # prevents F files from being read
        pattern = re.compile(r"^[A-Z]{3}([A-D]|\d)\d{2,3}[HY]\d?[SY]\d?.json$")
    for file_name in all_files:
        if not pattern.match(file_name):
            continue
        fnp = f"{session_name}/{file_name}"
        f_data = json.loads(jsonviewer.open_file(fnp))
        list_of_dicts.append(f_data)
        # print(f_data)
        dict_of_dicts[f_data["code"]] = f_data
    return list_of_dicts, dict_of_dicts


def list_get(li: list[int], ind: int, otherwise: int) -> int:
    """Return li[ind] if it exists, otherwise default."""
    if ind < len(li):
        return li[ind]
    else:
        return otherwise


def construct_existing_course(c_info: ci.Course) -> Course:
    """Constructs a course from exting course data"""
    return Course(c_info.get("title", "??"), c_info["code"], c_info["timeIntervals"], [
        construct_meeting(x['meetingNumber'], x["enrollmentLogs"], x["enrollmentCap"],
                          construct_cap(x.get("enrollmentCapComplex", None), ),
                          x.get('createdAt', list_get(c_info["timeIntervals"], 0, 0)),
                          construct_instructor_log(x.get('instructorLog', None)), x.get('delivery', 'INPER'),
                          x.get('instructors', [])
                          ) for x in c_info["meetings"]], )


def create_new_course(course_code: str, course_title: str) -> Course:
    """Attempts to create an entire new course that
    doesn't exist. Log a time at the previous second."""
    temp_course = Course(course_title, course_code, [int(TIME_RIGHT_NOW) - 1], [])
    return temp_course


@dataclass
class Course:
    """Represents a course offering.
    Attributes:
        - title: Calculus I
        - code: 'MAT135H1-F'
        - timeIntervals: [99399, 99999, 100249, ...]
        - meetings: its meetings
    """
    title: str
    code: str  # the code gives us enough info on whether a course is F/S/Y
    time_intervals: list[int]
    meetings: list[Meeting]
    faculty: str = "UNKNOWN"

    def has_lec(self) -> bool:
        return any(x.is_lec() for x in self.meetings)

    def has_tut(self) -> bool:
        return any(x.is_tut() for x in self.meetings)

    def has_pra(self) -> bool:
        return any(x.is_pra() for x in self.meetings)

    def no_course_info(self) -> bool:
        """Return whether this course has a meeting."""
        return len(self.meetings) == 0

    def get_title(self) -> str:
        for item in FORBIDDEN:
            if self.code.startswith(item):
                return "--"
        return self.title

    def export(self) -> dict:
        """Exports this class into a dictionary"""
        if self.has_lec():
            mt_ex = [m.export_dict() for m in self.meetings if m.is_lec()]
        elif self.has_pra():
            mt_ex = [m.export_dict() for m in self.meetings if m.is_pra()]
        else:
            mt_ex = [m.export_dict() for m in self.meetings if m.is_tut()]

        return {"title": self.get_title(), "code": self.code, "faculty": self.faculty,
                "timeIntervals": self.time_intervals,
                "meetings": mt_ex}

    def update_all_meetings(self, course_info: dict[str, str | dict | None], constants: Optional[list[dict[str, int]]]) -> None:
        """Update all the meetings stored within this course.

        :param course_info: an instance containing information about an entire course offering,
        such as MAT135H1-F
        """

        time_right_now = int(TIME_RIGHT_NOW)
        self.time_intervals.append(time_right_now)
        sections_list = course_info['sections']
        for section in sections_list:
            self._update_or_add_meeting(section, constants, course_info)

        temp_f = course_info["faculty"]["code"]
        self.faculty = temp_f if temp_f is not None else "UNKNOWN_FACULTY"

    def _update_or_add_meeting(self, section: dict[str, str | dict],
                               target_constant_data: Optional[list[dict[str, str | dict[str, int]]]],
                               course_info: dict) -> None:
        """Update an individual lecture section (LEC0701 for instance) of this course.
        If the lecture section wasn't there originally, add it.

        :param section: the information about the lecture section
        :return: nothing
        """

        # self.faculty = course_info["faculty"]["code"]
        # fc = ["ARTSC", "ARTSC", "ARTSC", "SCAR", "ARTSC", "ERIN"]
        waitlist_open = True
        if target_constant_data is not None:
            current_faculty = course_info["faculty"]["code"]
            if current_faculty is None or current_faculty not in {"ARTSC", "SCAR", "ERIN"}:
                if self.code[7] == "1":
                    current_faculty = "ARTSC"
                elif self.code[7] == "3":
                    current_faculty = "SCAR"
                elif self.code[7] == "5":
                    current_faculty = "ERIN"
            constants = next((y for y in target_constant_data if y["faculty"] == current_faculty), None)

            if constants is not None:
                fall_waitlist_closed = constants["importantTimestamps"].get("fallWaitlistClosed", None)
                winter_waitlist_closed = constants["importantTimestamps"].get("winterWaitlistClosed", None)
                # course code regexes are always AAA100Y1S
                is_winter = len(self.code) >= 9 and self.code[8] == "S"
                target_waitlist_closed = winter_waitlist_closed if is_winter else fall_waitlist_closed
                if target_waitlist_closed is not None and TIME_RIGHT_NOW > target_waitlist_closed:
                    waitlist_open = False

        # print(f"Waitlist for {self.code} is {'OPEN' if waitlist_open else 'CLOSED'}")
        meeting_num = section["name"]  # LEC0701
        instructor_info: list[dict[str, str]] = self.attempt_grab_ins(section)
        instructors = []
        for ins in instructor_info:
            if ins["firstName"] is not None and ins["lastName"] is not None:
                instructors.append(Instructor(ins["firstName"] or "", ins["lastName"] or ""))
        current_enrollment = int(section["currentEnrolment"] or 0) + (int(section["currentWaitlist"] or 0)
                                                                      if waitlist_open else 0)
        max_enrollment = int(section["maxEnrolment"] or 0)
        # in self.meetings, return the index of matching meeting_number
        # if not found, return -1
        target_meeting = self._find_or_create_meeting(meeting_num)

        delivery_mode = get_delivery_mode(section)

        target_meeting.update_meeting(current_enrollment, max_enrollment, instructors, self.time_intervals,
                                      delivery_mode, section.get("cancelInd", "N"))

    def attempt_grab_ins(self, section) -> list[dict[str, str]]:
        p1 = section["instructors"]
        if p1 is None:
            return []
        else:
            return p1

    def _find_or_create_meeting(self, meeting_number: str) -> Meeting:
        """Finds the meeting stored in this class, or creates a new one
        ready for updating if not already.

        :param meeting_number: LEC0701
        :return: that meeting
        """
        for met in self.meetings:
            if met.meeting_number == meeting_number:
                return met
        # if I couldn't find a meeting, create one, add it to the meetings list, and sort it
        new_meeting = create_new_meeting(meeting_number, self.time_intervals)
        self.meetings.append(new_meeting)
        self.meetings.sort(key=lambda x: x.meeting_number)  # sort meetings in the list by meeting number
        return new_meeting


def get_delivery_mode(section: dict[str, Any]) -> str:
    """Get the delivery mode for this course.
    A course better have only one delivery mode and better
    not switch to online mid-semester."""
    deliv = section.get('deliveryModes', None)
    if deliv is None:
        return 'INPER'
    else:
        if len(deliv) == 0:
            return 'INPER'
        else:
            # print(deliv[0]['mode'])
            return deliv[0]['mode']


def safe_empty_string(candidate_string: None | str) -> str:
    """If the string is none, make it an empty string"""
    return "" if candidate_string is None else candidate_string


def create_new_meeting(meeting_number: str, overall_time_logs: list[int]) -> Meeting:
    """Creates a new meeting. The new meeting should not attempt
    to record today - that will be done in a future step.

    The moment a meeting is created, zeroes are placed for all existing
    time logs. This is done in case a new meeting for an existing course was created.

    :param meeting_number: the meeting number, i.e. LEC0101
    :param overall_time_logs: overall time logs. Include the time right now of capture.
    :return: the meeting
    """
    temp_enrollment_log = [0 for _ in range(len(overall_time_logs) - 1)]
    return Meeting(meeting_number, [], temp_enrollment_log, -1, math.floor(TIME_RIGHT_NOW), None, None)


def construct_meeting(meeting_number: str, enrollment_logs: list[int], enrollment_cap: int,
                      cap_complex: Optional[ComplexEnrollmentCap], created_at: int,
                      instructor_log: Optional[InstructorLog], delivery: Optional[str],
                      instructor: Optional[list[dict[str, str]]]) -> Meeting:
    """Constructs a meeting given existing information.

    :param instructor: the instructor
    :param delivery: the delivery mode of the course
    :param instructor_log: the instructor log
    :param cap_complex: Complex enrollment cap
    :param meeting_number: LEC0101
    :param enrollment_logs: self-explanatory (existing)
    :param enrollment_cap: the cap
    :return: the meeting object
    :param created_at: when this meeting was added. If not in the JSON already, created_at
    is the first number.
    """
    if instructor is None:
        instructor_list = []
    else:
        instructor_list = []
        for item in instructor:
            instructor_list.append(Instructor(item["firstName"], item["lastName"]))
    if delivery is None:
        delivery = 'INPER'
    return Meeting(meeting_number, instructor_list, enrollment_logs, enrollment_cap, created_at, cap_complex,
                   instructor_log,
                   delivery)


def construct_cap(existing_info: Optional[dict[str, Union[list[dict[str, int]], int]]]) -> ComplexEnrollmentCap:
    return ComplexEnrollmentCap(existing_info["initialCap"],
                                [ComplexCapEntry(x['time'], x['newCapacity']) for x in
                                 existing_info["capChanges"]]) if existing_info is not None else None


@dataclass
class ComplexCapEntry:
    """time: int, new_capacity: int"""
    time: int
    new_capacity: int

    def export_dict(self) -> dict[str, int]:
        return {"time": self.time, "newCapacity": self.new_capacity}


class ComplexEnrollmentCap:
    """Represents an enrollment cap that
    is capable of recording changes. Assume
    that a capture is never done twice in
    a row."""
    initial_cap: int
    cap_changes: list[ComplexCapEntry]  # [TIME, CAP]

    def __init__(self, initial_cap: int, cap_changes: Optional[list[ComplexCapEntry]] = None) -> None:
        self.initial_cap = initial_cap
        self.cap_changes = [] if cap_changes is None else cap_changes

    def update_complex_cap(self, cur_time: int, cur_cap: int) -> None:
        """Update the enrollment cap.

        :param cur_time: The current time right now, in seconds
        since Jan 1, 1970.
        :param cur_cap: The maximum capacity of this course right now.
        """
        # the default cap is -10. If the initial cap is less than 0, then only
        # change the initial cap.
        if self.initial_cap < 0 and len(self.cap_changes) == 0:
            self.initial_cap = cur_cap
            return
        previous_cap = self.cap_changes[-1].new_capacity if len(self.cap_changes) != 0 else self.initial_cap
        if previous_cap != cur_cap:
            self.cap_changes.append(ComplexCapEntry(cur_time, cur_cap))

    def export_dict(self) -> dict[str, Any]:
        return {"initialCap": self.initial_cap, "capChanges": [x.export_dict() for x in self.cap_changes]}


def construct_instructor_log(ins_raw: Optional[ci.InstructorLog]) -> Optional[InstructorLog]:
    """Construct an instructor log. The input is always the dictionary
    Exported from the instructor log class
    """
    if ins_raw is None:
        return None
    initial_instructors_list = construct_ins_from_ins_raw_log(ins_raw)
    return InstructorLog(
        initial_instructors_list,
        [InstructorChange(construct_ins_from_ins_list(x['instructorsAfter']), x['timing'])
         for x in ins_raw['instructorChanges']]
    )


def construct_ins_from_ins_raw_log(ins_raw_log: ci.InstructorLog) -> list[Instructor]:
    initial_instructors_list = []
    for item in ins_raw_log['initialInstructors']:
        initial_instructors_list.append(Instructor(item['firstName'], item['lastName']))
    return initial_instructors_list


def construct_ins_from_ins_list(ins_list: list[ci.Instructor]) -> list[Instructor]:
    initial_instructors_list = []
    for item in ins_list:
        initial_instructors_list.append(Instructor(item['firstName'], item['lastName']))
    return initial_instructors_list


def compare_ins_list(l1: list[Instructor], l2: list[Instructor]) -> bool:
    for i1 in l1:
        if not any(x.ins_equal(i1) for x in l2):
            return False
    for i2 in l2:
        if not any(y.ins_equal(i2) for y in l1):
            return False
    return True


class InstructorLog:
    initial_instructors: list[Instructor]
    instructor_changes: list[InstructorChange]

    def __init__(self, initial_instructors: list[Instructor],
                 instructor_changes: Optional[list[InstructorChange]] = None) -> None:
        """Builds this class.
        The initial instructors must always be stated, but any changes in instructors
        must always be stated if the existing class is being updated. If created
        for the first time, just leave instructor_changes blank and feed
        the initial instructors the default value.
        """
        self.initial_instructors = initial_instructors
        self.instructor_changes = [] if instructor_changes is None else instructor_changes

    def attempt_update_instructors(self, ins: list[Instructor]) -> None:
        """Attempt to update the instructors for this course.
        An instructor will only update if the instructor list
        is different, where I don't look at order.

        Otherwise, do nothing.
        """

        if len(self.instructor_changes) == 0:
            last_ins = self.initial_instructors
        else:
            last_ins = self.instructor_changes[-1].instructors_after
        if not compare_ins_list(last_ins, ins):
            temp_ins_change = InstructorChange(ins, int(TIME_RIGHT_NOW))
            self.instructor_changes.append(temp_ins_change)
        # otherwise, the instructors wouldn't have changed, and I won't
        # log anything.

    def export_dict(self) -> ci.InstructorLog:
        return {
            "initialInstructors": [w.export_dict() for w in self.initial_instructors],
            "instructorChanges": [x.export_dict() for x in self.instructor_changes]
        }


@dataclass
class InstructorChange:
    """Represents an instructor change.
    instructors_after is the instructors after timing
    """
    instructors_after: list[Instructor]
    timing: int

    def export_dict(self) -> dict:
        return {
            "instructorsAfter": [w.export_dict() for w in self.instructors_after],
            "timing": self.timing
        }


def build_instructor(temp: Union[str, list[str]]) -> list[str]:
    if isinstance(temp, str):
        return [z.strip() for z in temp.split(", ")]
    if isinstance(temp, list):
        return temp


@dataclass
class Instructor:
    first_name: str
    last_name: str

    def export_dict(self) -> ci.Instructor:
        return {"firstName": self.first_name, "lastName": self.last_name}

    def ins_equal(self, other: Instructor) -> bool:
        return self.first_name == other.first_name and self.last_name == other.last_name


# @dataclass
class Meeting:
    """Attributes:
        - meeting_number: LEC0101
        - instructors: ['Firstname Lastname', ...]
        - enrollment_logs: [0, 1, 2, 3, 4, 5]
        - enrollment_cap: 65
    """
    meeting_number: str
    instructors: list[Instructor]
    instructor_log: InstructorLog
    enrollment_logs: list[int]
    enrollment_cap: int
    enrollment_cap_complex: ComplexEnrollmentCap
    created_at: int  # the time this meeting was created
    delivery: str
    is_cancelled: bool

    def __init__(self, meeting_number: str, instructors: list[Instructor], enrollment_logs: list[int],
                 enrollment_cap: int,
                 created_at: int, enrollment_cap_complex: Optional[ComplexEnrollmentCap] = None,
                 instructor_log: Optional[InstructorLog] = None, delivery: str = 'INPER',
                 cancelled: bool = False
                 ) -> None:
        """Constructs this meeting, either for first time use or subsequent use."""
        self.meeting_number = meeting_number
        self.instructors = instructors
        self.enrollment_logs = enrollment_logs
        self.enrollment_cap = enrollment_cap
        self.enrollment_cap_complex = enrollment_cap_complex if enrollment_cap_complex is not None else \
            ComplexEnrollmentCap(
                enrollment_cap
            )
        self.instructor_log = instructor_log if instructor_log is not None else \
            InstructorLog(
                instructors
            )

        self.created_at = created_at
        self.delivery = delivery
        self.is_cancelled = cancelled

    def is_lec(self) -> bool:
        return self.meeting_number.startswith("LEC")

    def is_tut(self) -> bool:
        return self.meeting_number.startswith("TUT")

    def is_pra(self) -> bool:
        return self.meeting_number.startswith("PRA")

    def export_dict(self) -> ci.Meeting:
        return {"meetingNumber": self.meeting_number,
                "instructors": [
                    x.export_dict() for x in self.instructors],
                "instructorLog": self.instructor_log.export_dict(),
                "enrollmentLogs": self.enrollment_logs, "enrollmentCap": self.enrollment_cap,
                "enrollmentCapComplex": self.enrollment_cap_complex.export_dict() if self.enrollment_cap_complex is not None else None,
                "createdAt": self.created_at,
                "delivery": self.delivery,
                "isCancelled": self.is_cancelled}

    def update_meeting(self, enroll: int, enroll_cap: int, instructors: list[Instructor],
                       overall_time_logs: list[int], delivery: str, cancelled: str) -> None:
        """Update the information for this meeting.

        :param delivery: if the course
        :param enroll: the number of students enrolled in the course right now.
        :param enroll_cap: the capacity of enrollment for this course.
        :param instructors: a list of instructors for this course. Any format is okay.
        :param overall_time_logs: in the course class, please pass the overall time logs - it is
        needed for alignment purposes. The time logs must include the time it is capturing right now.
        """

        if cancelled == 'Y':
            self.is_cancelled = True
            enroll_cap = 0  # if the course is cancelled, the enroll cap will always be set to 0
            enroll = 0
        else:
            self.is_cancelled = False

        # helps ensure that the enrollment logs' length is consistent
        self.delivery = delivery
        while len(self.enrollment_logs) < len(overall_time_logs) - 1:
            if len(self.enrollment_logs) == 0:
                self.enrollment_logs.append(0)
            else:
                self.enrollment_logs.append(self.enrollment_logs[-1])

        # append the current enrollment
        self.enrollment_logs.append(enroll)
        assert len(self.enrollment_logs) == len(overall_time_logs)
        # make sure the other variables are up-to-date
        self.enrollment_cap = enroll_cap
        if instructors:
            self.instructors = instructors
            self.instructor_log.attempt_update_instructors(instructors)

        if self.enrollment_cap_complex is not None and len(overall_time_logs) > 0:
            self.enrollment_cap_complex.update_complex_cap(overall_time_logs[-1], enroll_cap)


def create_folder_if_not_exists(folder_path: str) -> None:
    if not os.path.exists(folder_path):
        try:
            os.makedirs(folder_path)
        except OSError as e:
            print(f"Error creating folder '{folder_path}': {e}")


def main(sessions: list[str], session_name: str, fall_over: bool = False):
    """Scrap all courses and push their changes.
    :param sessions: all sessions to search as accepted by TTB.
    :param session_name: the session name to be read by the timetable tracker app.
    """
    global TIME_RIGHT_NOW
    TIME_RIGHT_NOW = time.time()
    run_this(sessions, session_name, fall_over)
