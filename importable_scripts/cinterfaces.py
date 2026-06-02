from typing import TypedDict, List, Optional


class Course(TypedDict):
    title: str
    code: str
    faculty: str
    timeIntervals: List[int]
    meetings: List['Meeting']


class EnrollmentCapChange(TypedDict):
    time: int
    newCapacity: int


class EnrollmentCapComplex(TypedDict):
    capChanges: List[EnrollmentCapChange]
    initialCap: int


class Instructor(TypedDict):
    firstName: str
    lastName: str


class InstructorChangeInstance(TypedDict):
    instructorsAfter: List[Instructor]
    timing: int


class InstructorLog(TypedDict):
    initialInstructors: List[Instructor]
    instructorChanges: List[InstructorChangeInstance]


class Meeting(TypedDict):
    meetingNumber: str
    createdAt: int
    instructors: List[Instructor]
    enrollmentLogs: List[int]
    enrollmentCap: int
    enrollmentCapComplex: Optional[EnrollmentCapComplex]
    instructorLog: Optional[InstructorLog]
    delivery: Optional[str]
    isCancelled: Optional[bool]


class ImportantTimestampsBundle(TypedDict):
    faculty: str
    importantTimestamps: 'ImportantTimestamps'


class ImportantTimestamps(TypedDict):
    start: int
    fourth: Optional[int]
    third: Optional[int]
    second: Optional[int]
    first: Optional[int]
    general: int
    fallFirstDay: int
    fallWaitlistClosed: int
    fallEnrollmentEnd: int
    fallDrop: int
    fallLWD: int
    winterStart: int
    winterWaitlistClosed: int
    winterEnrollmentEnd: int
    yearDrop: int
    winterDrop: int
    winterLWD: int
    endOfYear: int
    fall75: Optional[int]
    fall50: Optional[int]
    winter75: Optional[int]
    winter50: Optional[int]
    year75: Optional[int]
    year50: Optional[int]
    isSummer: Optional[bool]


class SessionsRaw(TypedDict):
    sessions: List['SessionInfo']


class SessionInfo(TypedDict):
    sessionCode: str
    name: str


class SessionCollection(TypedDict):
    sessions: List['IndividualSessionInfo']
    default: str


class IndividualSessionInfo(TypedDict):
    sessionCode: str
    name: str


class TopCourses(TypedDict):
    courses: List[str]
