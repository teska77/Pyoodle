from unittest import TestCase
import os, pprint
from pyoodle import Moodle, MoodleCourseViewer


class TestMoodleCourseViewer(TestCase):
    def setUp(self) -> None:
        print(os.getenv("moodle-dl-host"), os.getenv("moodle-dl-cookie"))
        self.mInfo = Moodle(host=os.getenv("moodle-dl-host"), cookie=os.getenv("moodle-dl-cookie"))
        self.viewer = MoodleCourseViewer(self.mInfo)

    def test_get_main_categories(self):
        categories = self.viewer.get_main_categories()
        pprint.pp(categories)
        self.assertGreater(len(categories), 0)

    def test_get_subjects(self):
        # Assuming that we have selected a menu option here
        subjects = self.viewer.get_subject_list(12)
        pprint.pp(subjects)
        self.assertGreater(len(subjects), 0)

    def test_get_courses(self):
        courses = self.viewer.get_course_list(39)
        pprint.pp(courses)
        self.assertGreater(len(courses), 0)
        for course in courses.values():
            print(course['url'])
