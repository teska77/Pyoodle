from unittest import TestCase
from src.pyoodle import Moodle, MoodleResourceDownloader, MoodleResourceParser

class TestMoodleResourceDownloader(TestCase):
    def setUp(self) -> None:
        self.mInfo = Moodle("https://moodle.royalholloway.ac.uk", cookie="REDACTED")
        self.mParser = MoodleResourceParser(self.mInfo, 3933)

    def test_download(self):
        mDownloader = MoodleResourceDownloader(self.mInfo, self.mParser)
        mDownloader.download_mapping("2")
        mDownloader.download_url("https://moodle.royalholloway.ac.uk/mod/resource/view.php?id=461341", "test.pdf")
