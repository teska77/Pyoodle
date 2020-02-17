from unittest import TestCase
from src.pyoodle import Moodle, MoodleResourceParser
import json, pprint


class TestMoodleResourceParser(TestCase):
    def setUp(self) -> None:
        self.mInfo = Moodle("https://moodle.royalholloway.ac.uk", cookie="REDACTED")

    def test_find_resources(self):
        mparser = MoodleResourceParser(self.mInfo, 3933)
        print(json.dumps(mparser.find_resources(), indent=4))
        mparser.print_resources()
        pprint.PrettyPrinter(indent=4).pprint(mparser.fill_resource_map())
