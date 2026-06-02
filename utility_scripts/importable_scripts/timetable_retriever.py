"""Script that is responsible for downloading"""


import json
import math
from typing import Union

import requests

# open coursesMAT.json

PAGE_SIZE = 20


def open_file(file: str, allow_exceptions: bool = False) -> str:
    """Return file contents of any plain text file in the directory file.
    """
    if not allow_exceptions:
        with open(file, encoding='UTF-8') as f:
            file_text = f.read()
        return file_text
    else:
        try:
            with open(file, encoding='UTF-8') as f:
                file_text = f.read()
            return file_text
        except FileNotFoundError:
            return ''


def write_file(text: str, filename: str) -> None:
    """Write file with given name.
    """
    with open(filename, 'w', encoding='UTF-8') as f:
        f.write(text)


def get_json(file_path: str) -> dict:
    """a method that has one argument: a file path that is a json, that returns the json as a dict"""
    with open(file_path) as f:
        return json.load(f)


def get_stuff_2(sessions: Union[list[str], None] = None) -> dict:
    """Grab all data from the timetable builder API
    and return it here. The returned format is clean

    sessions replaces the existing sessions argument, if specified.

    :return: all the content from the timetable builder
    """
    MAX_PAGES = 99999999999
    temp: dict = get_json("tq.json")

    if sessions is not None:
        temp["sessions"] = sessions

    temp["pageSize"] = PAGE_SIZE

    ttb_link = open_file('ttb_link.txt', False).strip()  # an error is thrown otherwise

    r = requests.post(ttb_link, json=temp, headers={
        "Accept": "application/json"
    })
    # to_dict: {course: course[], total: int, page: int, pageSize: int}
    to_dict = json.loads(r.content)['payload']['pageableCourse']

    total = to_dict["total"]
    page = 1
    page_size = to_dict["pageSize"]

    assert (page_size == PAGE_SIZE)

    courses = []
    courses += to_dict["courses"]
    print("Doing this")
    total_pages = math.ceil(total / PAGE_SIZE)
    for i in range(2, total_pages + 1):
        if i > MAX_PAGES:
            break
        print(f"Getting page {i}/{total_pages}")
        pass  # i is the current page
        temp["page"] = i
        req2 = requests.post(ttb_link, json=temp, headers={
            "Accept": "application/json"
        })
        # to_dict: {course: course[], total: int, page: int, pageSize: int}
        pageable_course_2 = json.loads(req2.content)['payload']['pageableCourse']
        courses += pageable_course_2["courses"]

    return {"courses": courses}
