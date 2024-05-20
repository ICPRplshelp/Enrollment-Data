# Enrollment Tracker Data

This repository contains all data when it comes to tracking enrollments,
primarily created for [this](https://github.com/ICPRplshelp/UofT-Enrollment-Tracker).

## Notes

All data is updated by me.

**IMPORTANT:**

- If you're going to use the data in any way, do not use Git to fetch it, as I could change how I host this later.
- On July 17, 2023, the way that enrollment data is stored has changed.

## Where is all the data from?

https://ttb.utoronto.ca/

## Specifications

If you want to fork this, make sure your fork meets this format:

### Sessions

Sessions are either Fall/Winter or Summer. Their folder names will be:

`${current_year}${5 if summer else 9}`

For example, Fall-Winter 2024-2025 is coded "20249", and Summer 2024 is
coded "20245"

### Constant JSON files

These files must be in the session folder. They start with `AA` so they are hoisted.

- `AAclistall.json`: To ensure autocomplete works
- `AAtcconstants.json`: Important dates in UNIX time. Unix time is midnight ET; these are "time points", i.e. if Nov 9th is the last day to drop, Nov. 10 at 12AM will be recorded there as Unix time.
- `aaTopCourses.json`: Default courses for this session, usually a list of the most popular courses in that session.


<!--
To generate these files, run 

```
cd utility_scripts
python generate_autocomplete.py <SESSION>
python generate_constants.py <SESSION>
python generate_top_courses.py <SESSION>

```
-->