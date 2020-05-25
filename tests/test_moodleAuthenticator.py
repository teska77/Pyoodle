from unittest import TestCase
from src.pyoodle import MoodleAuthenticator, Moodle
import requests, time, os, base64


class TestMoodleAuthenticator(TestCase):
    def setUp(self) -> None:
        self.mInfo = Moodle(os.getenv("moodle-dl-host"), username=os.getenv("moodle-dl-username"),
                            password=str(base64.b64decode(os.getenv("moodle-dl-password"))))
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
