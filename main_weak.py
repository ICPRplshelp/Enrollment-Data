"""Running this automatically updates all entries based on the current day.
No need to specify the session, it is auto-determined by the date today."""

import requests
from datetime import datetime, date
import retriever_updater
try:
    from update_git import push
except ImportError:
    push = lambda: print("Push: Done")


def ytd_today() -> int:
    today = date.today()
    return today.timetuple().tm_yday


def which_sessions_should_i_run() -> list[tuple[list[str], str]]:
    """Which sessions should I run"""
    dt = date.today()
    current_year = dt.year
    cl_a = []
    # summer
    if date(current_year, 2, 17) <= dt <= date(current_year, 8, 20):
        cl_a.append(([f"{current_year}5", f"{current_year}5F", f"{current_year}5S"], f"{current_year}5"))
    # fall-winter
    if dt < date(current_year, 1, 19):
        last_year = current_year - 1
        cl_a.append(([f"{last_year}9", f"{current_year}1", f"{last_year}9-{current_year}1"], f"{last_year}9"))
    elif date(current_year, 1, 19) <= dt < date(current_year, 4, 25):
        last_year = current_year - 1
        cl_a.append(([f"{current_year}1", f"{last_year}9-{current_year}1"], f"{last_year}9"))
    elif date(current_year, 6, 12) <= dt:
        next_year = current_year + 1
        cl_a.append(([f"{current_year}9", f"{next_year}1", f"{current_year}9-{next_year}1"], f"{current_year}9"))
    return cl_a


def run_main_weak(ses: list[str], ses_name: str) -> bool:
    try:
        retriever_updater.main(ses, ses_name)
    except requests.exceptions.ConnectionError:
        print("Couldn't get it this time!!!")
        return False
    print('trying to push')
    return True


def run_main_auto():
    for ses_l, ses_n in which_sessions_should_i_run():
        print(f"{ses_l=} {ses_n=}")
        run_main_weak(ses_l, ses_n)
    push()


if __name__ == "__main__":
    # the last argument must always be false
    run_main_auto()
