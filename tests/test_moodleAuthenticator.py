from unittest import TestCase
from src.pyoodle import MoodleAuthenticator, Moodle
import requests, time


class TestMoodleAuthenticator(TestCase):
    def setUp(self) -> None:
        self.mInfo = Moodle("https://moodle.royalholloway.ac.uk", username="REDACTED", password="REDACTED")
        self.m_authenticator = MoodleAuthenticator(self.mInfo, DEBUG_LEVEL=4)

    def test_get_login_attributes(self):
        cookies, logintoken, anchor = self.m_authenticator.get_login_attributes()
        print(cookies, anchor, logintoken)
        self.assertEqual(anchor, '')
        self.assertIsNotNone(cookies)
        self.assertIsNotNone(logintoken)

    def test_send_request(self):
        cookies, logintoken, anchor = self.m_authenticator.get_login_attributes()
        print(cookies, anchor, logintoken)
        time.sleep(2)
        self.m_authenticator.send_request(logintoken, anchor)
