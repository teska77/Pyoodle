from unittest import TestCase
from src.pyoodle import Moodle, MoodleCourseFinder

class TestMoodleCourseFinder(TestCase):
    def setUp(self) -> None:
        self.mInfo = Moodle("https://moodle.royalholloway.ac.uk", cookie="REDACTED")

    def test_find_courses(self):
        mfinder = MoodleCourseFinder(self.mInfo)
        print(mfinder.find_courses())
        mfinder.print_courses()
