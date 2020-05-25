#!/usr/bin/env python3

# This horrifying project has been brought to you by Teska!

import argparse
import json
import os
import re
import shutil
import sys
import time
import pprint
from getpass import getpass

import requests
from bs4 import BeautifulSoup


class InvalidLogin(Exception):
    pass


class Moodle:
    def __init__(self, host, username=None, password=None, cookie=None, debug_level=1, save_dir=os.getcwd(),
                 make_dir=True, file_name=2):
        self.host = host
        self.username = username
        self.password = password
        self.cookie = cookie
        self.session = requests.Session()
        self.debug_level = debug_level
        self.save_dir = save_dir
        self.make_dir = make_dir
        self.file_name = file_name
        self.sess_key = None
        if cookie:
            self.session.cookies["MoodleSession"] = cookie
        if not host or (not username and not password and not cookie):
            print("A host must be provided in addition to either credentials or an existing session cookie.")
            sys.exit(1)

    def get_session_key(self):
        try:
            response = self.session.get("{}/my".format(self.host))
            soup = BeautifulSoup(response.content, 'html.parser')
            self.sess_key = soup.find(attrs={"name": "sesskey"})['value']
            return self.sess_key
        except requests.exceptions.RequestException:
            print("Error fetching session ID!")
            raise requests.exceptions.RequestException


class MoodleAuthenticator:

    def __init__(self, moodle, session=None, DEBUG_LEVEL=1):
        self.host = moodle.host
        self.username = moodle.username
        self.password = moodle.password
        self.DEBUG_LEVEL = DEBUG_LEVEL
        self.cookie = None
        if not session:
            self.session = moodle.session

    def get_login_attributes(self):
        try:
            response = self.session.get(self.host)
            response = self.session.get(
                url="{}/login/index.php".format(self.host),
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Connection": "keep-alive",
                    "Accept-Encoding": "br, gzip, deflate"
                },
                verify=False
            )
            if self.DEBUG_LEVEL >= 4:
                print('Response HTTP Status Code: {status_code}'.format(
                    status_code=response.status_code))
                print('Response HTTP Response Body: {content}'.format(
                    content=response.content))
                print('Moodle Cookie: {}'.format(self.session.cookies.get("MoodleSession")))
            soup = BeautifulSoup(response.content, 'html.parser')
            anchor = soup.find(attrs={"id": "anchor", "name": "anchor"})['value']
            login_token = soup.find(attrs={"name": "logintoken"})['value']
            self.cookie = self.session.cookies.get("MoodleSession")
            return self.cookie, login_token, anchor

        except requests.exceptions.RequestException:
            print('HTTP Request failed')

    def send_request(self, token, anchor):
        login_result = False
        try:
            response = self.session.post(
                url="{}/login/index.php".format(self.host),
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept-Encoding": "br, gzip, deflate",
                    "Connection": "keep-alive",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
                data="username={}&password={}&anchor={}&logintoken={}".format(self.username, self.password, anchor,
                                                                              token),
            )
            if self.DEBUG_LEVEL >= 4:
                print('Response HTTP Status Code: {status_code}'.format(
                    status_code=response.status_code))
                print('Response HTTP Response Body: {content}'.format(
                    content=response.content))
                print(response.history)
                print(response.headers)
                print(response.request.headers)
                print(self.session.cookies)
            if self.DEBUG_LEVEL >= 2:
                print('New Cookie: {}'.format(self.session.cookies.get("MoodleSession")))
            if "{}/login/index.php" in response.url:
                raise InvalidLogin
            return self.session.cookies.get("MoodleSession")
        except requests.exceptions.RequestException:
            print('HTTP Request failed')

    def get_session(self) -> requests.Session:
        cookie, token, anchor = self.get_login_attributes()
        # Wait a bit to satisfy the server that we are real...
        time.sleep(0.5)
        self.cookie = self.send_request(token, anchor)

        # We are now logged in, hand over the request session to the next object
        return self.session


class MoodleCourseViewer:

    def __init__(self, moodle: Moodle):
        self.host = moodle.host
        self.session = moodle.session
        self.sess_key = moodle.sess_key
        self.debug_level = moodle.debug_level
        self.categories = {}

    def get_main_categories(self):
        self.categories = self.get_categories(f"{self.host}/course/index.php")
        return self.categories

    def get_categories(self, url):
        category_map = {}
        response = self.session.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        categories = soup.findAll(attrs={"class": "category"})  # Moodle separates each course category via a
        # 'category' class attribute
        for category in categories:
            link_name = category.find('a', href=True).text
            link_url = category.find('a', href=True)['href']
            link_id = category['data-categoryid']
            category_map[link_name] = {"id": link_id, "url": link_url}
        return category_map

    def get_subject_list(self, subject_id):
        subject_map = {}
        # We use 'perpage=0' here to make sure that all subjects are displayed on one page
        response = self.session.get(f"{self.host}/course/index.php?categoryid={str(subject_id)}&perpage=0")
        soup = BeautifulSoup(response.content, 'html.parser')
        subjects = soup.findAll(attrs={"class": "category"})
        for subject in subjects:
            link_name = subject.find('a', href=True).text
            link_url = subject.find('a', href=True)['href']
            link_id = subject['data-categoryid']
            subject_map[link_name] = {"id": link_id, "url": link_url}
        return subject_map

    def get_course_list(self, course_id):
        course_map = {}
        # We use 'perpage=0' here to make sure that all subjects are displayed on one page
        response = self.session.get(f"{self.host}/course/index.php?categoryid={course_id}&perpage=0")
        soup = BeautifulSoup(response.content, 'html.parser')
        courses = soup.findAll(attrs={"class": "coursename"})
        for course in courses:
            link_name = course.find('a', href=True).text
            link_url = course.find('a', href=True)['href']
            # Try to find the ID without scraping the url:
            try:
                link_id = course.parent.parent['data-courseid']  # Preferred method
            except KeyError:
                # We will have to get the course ID from the URL instead
                # First, find a pattern that matches `?id=xxxx' in a URL, get the first (and only) result using [0],
                # then cut the first four characters off (remove `?id=`). Finally, convert the id string to an int
                link_id = int(re.findall(r"\?id=\d+", link_url)[0][4:])
            course_map[link_name] = {"id": link_id, "url": link_url}
        return course_map


class MoodleCourseFinder:

    def __init__(self, moodle: Moodle):
        self.host = moodle.host
        self.session = moodle.session
        self.sess_key = moodle.sess_key
        self.debug_level = moodle.debug_level
        self.courses = []
        self.find_courses()

    def find_courses(self):
        try:
            response = self.session.post(
                url="{}/lib/ajax/service.php".format(self.host),
                params={
                    "sesskey": self.sess_key,
                    "info": "core_course_get_enrolled_courses_by_timeline_classification",
                },
                headers={
                    "Content-Type": "text/plain; charset=utf-8",
                },
                data="[{\"index\":0,\"methodname\":\"core_course_get_recent_courses\",\"args\":{\"limit\":20}}]"
            )
            if self.debug_level >= 4:
                print('Response HTTP Status Code: {status_code}'.format(
                    status_code=response.status_code))
                print('Response HTTP Response Body: {content}'.format(
                    content=response.content))
            json_response = json.loads(response.content)[0]
            if not json_response['error']:
                self.courses = json_response['data']
                return self.courses
            else:
                return []
        except requests.exceptions.RequestException:
            print('HTTP Request failed')

    def print_courses(self):
        if self.courses:
            course_num = 1
            for course in self.courses:
                print("{}.\t{}".format(course_num, course['fullname']))
                course_num += 1


class MoodleResourceParser:

    def __init__(self, moodle: Moodle, course_id: int):
        self.host = moodle.host
        self.session = moodle.session
        self.sess_key = moodle.sess_key
        self.course_id = course_id
        self.course_name = None
        self.course_code = None
        self.resources = []
        self.resource_map = {}
        self.contents = []
        self.find_resources()
        self.fill_resource_map()

    def find_resources(self):
        try:
            response = self.session.get("{}/course/view.php?id={}".format(self.host, self.course_id))
            self.course_code, self.course_name = self.get_course_info(response.text)
            soup = BeautifulSoup(response.content, 'html.parser')
            sections = soup.find_all(attrs={"class": "section"})
            for section in sections:
                section_name = section.find(attrs={"class": "sectionname"})
                if not section_name:
                    continue
                section_name = section_name.next
                temp_section = {"section": section_name, "contents": []}
                files = section.find_all(attrs={"class": "resource", "class": "modtype_resource"})
                for file in files:
                    f_name = file.find(attrs={"class": "instancename"}).next
                    f_url = file.a['href']
                    self.resources.append((f_name, f_url))
                    temp_section['contents'].append({"name": f_name, "type": "file", "url": f_url})
                folders = section.find_all(attrs={"class": "folder", "class": "modtype_folder"})
                for folder in folders:
                    f_name = folder.find(attrs={"class": "instancename"}).next
                    f_url = folder.a['href']
                    resources = self.find_resources_in_folder(f_url)
                    temp_folder = {"name": f_name, "type": "folder", "url": f_url, "contents": []}
                    for resource in resources:
                        temp_folder["contents"].append({"name": resource[0], "type": "file", "url": resource[1]})
                    temp_section["contents"].append(temp_folder)
                self.contents.append(temp_section)
            return self.contents
        except Exception as ex:
            raise ex

    def get_course_info(self, source):
        title_to_strip = re.findall(r"<title>.*?</title>", source)[0]
        title = re.sub("<[^>]*>", "", title_to_strip)
        course_code = re.findall("[A-Z]{2}[0-9]{4}", title)[0]
        try:
            split_title = title.split(course_code + ": ")[1]
        except IndexError:
            split_title = title
        return course_code, split_title

    def find_resources_in_folder(self, folder):
        results = []
        response = self.session.get(folder)
        soup = BeautifulSoup(response.content, 'html.parser')
        files = soup.find_all(attrs={"class": "fp-filename-icon"})
        for file in files:
            if not file.a:
                continue
            f_name = file.find(attrs={"class": "fp-filename"}).next
            f_url = file.a['href']
            results.append((f_name, f_url))
            self.resources.append((f_name, f_url))
        return results

    def fill_resource_map(self):
        section_counter = 1
        for section in self.contents:
            self.resource_map['{}'.format(section_counter)] = []
            resource_counter = 1
            for resource in section["contents"]:
                self.resource_map['{}.{}'.format(section_counter, resource_counter)] = []
                if resource['type'] == "file":
                    self.resource_map['{}'.format(section_counter)].append((resource['name'], resource['url']))
                    self.resource_map['{}.{}'.format(section_counter, resource_counter)].append((resource['name'],
                                                                                                 resource['url']))
                if resource['type'] == "folder":
                    file_counter = 1
                    for file in resource["contents"]:
                        self.resource_map['{}'.format(section_counter)].append((file['name'], file['url']))
                        self.resource_map['{}.{}'.format(section_counter, resource_counter)].append((file['name'],
                                                                                                     file['url']))
                        self.resource_map['{}.{}.{}'.format(section_counter, resource_counter, file_counter)] = []
                        self.resource_map['{}.{}.{}'.format(section_counter, resource_counter, file_counter)].append(
                            (file['name'], file['url']))
                        file_counter += 1
                resource_counter += 1
            section_counter += 1
        return self.resource_map

    def print_resources(self):
        section_counter = 1
        for section in self.contents:
            print("{}.\t{}".format(section_counter, section['section']))
            resource_counter = 1
            for resource in section["contents"]:
                print("\t{}.{}\t{}".format(section_counter, resource_counter, resource['name']))
                if resource['type'] == "folder":
                    file_counter = 1
                    for file in resource["contents"]:
                        print("\t\t{}.{}.{}\t{}".format(section_counter, resource_counter, file_counter, file['name']))
                        file_counter += 1
                resource_counter += 1
            section_counter += 1


class MoodleResourceDownloader:

    def __init__(self, moodle: Moodle, parser: MoodleResourceParser):
        self.host = moodle.host
        self.session = moodle.session
        self.save_dir = moodle.save_dir
        self.make_dir = moodle.make_dir
        self.file_name_mode = moodle.file_name
        self.parser = parser

    def download_mapping(self, map_key):
        if map_key in self.parser.resource_map:
            current = 1
            total = len(self.parser.resource_map.get(map_key))
            print()
            for file in self.parser.resource_map.get(map_key):
                printstr = "Downloading resource {} out of {}: {}...".format(str(current), str(total), file[0])
                print(printstr.ljust(shutil.get_terminal_size().columns), end="\r")
                self.download_url(file[1], file[0])
                current += 1
            print()

    def download_all(self):
        current = 1
        total = len(self.parser.resources)
        print()
        for file, url in self.parser.resources:
            printstr = "Downloading resource {} out of {}: {}...".format(str(current), str(total), file)
            print(printstr.ljust(shutil.get_terminal_size().columns), end="\r")
            self.download_url(url, file)
            current += 1

    def download_url(self, url, moodle_name=None):
        try:
            response = self.session.get(url)
            try:
                server_filename = re.findall(r'"(.*?)"', response.headers.get("content-disposition"))[0]
            except TypeError:
                print("Error: Could not get server name for this file, relying on moodle name")
                server_filename = moodle_name
            if self.file_name_mode == 2:
                filename = moodle_name + " - " + server_filename
            elif self.file_name_mode == 1:
                filename = moodle_name
            else:
                filename = server_filename
            # Strip any unfriendly characters from the filename
            filename = filename.replace("/", "-").replace(":", "-").replace("%20", " ").replace("$", "")
            directory = os.path.join(self.save_dir, self.parser.course_code)
            if self.make_dir:
                if not os.path.exists(directory):
                    os.mkdir(directory)

            with open(os.path.join(directory, filename), 'wb') as writer:
                for chunk in response.iter_content(chunk_size=128):
                    writer.write(chunk)
                writer.close()
        except requests.exceptions.RequestException:
            pass


def load_config_file(config_location):
    try:
        reader = open(config_location, 'r')
        config = json.load(reader)
        # Initialize anything missing to a None Type
        if not 'host' in config:
            config['host'] = None
        if not 'username' in config:
            config['username'] = None
        if not 'password' in config:
            config['password'] = None
        if not 'cookie' in config:
            config['cookie'] = None
        if not 'course' in config:
            config['course'] = None
        if not 'directory' in config:
            config['directory'] = None
        reader.close()
    except FileNotFoundError:
        print("The specified config file does not exist!")
        sys.exit(1)
    return config


def config_exists(config_location):
    return os.path.exists(config_location)


def clear():
    print("\n" * shutil.get_terminal_size().lines)


def show_courses():
    course_finder = MoodleCourseFinder(moodle)
    clear()
    print("Most recent courses accessed")
    course_finder.print_courses()
    return course_finder


def show_files(course_name, course_id):
    clear()
    print("Loading resources for {}...".format(course_name))
    course_parser = MoodleResourceParser(moodle, course_id)
    course_parser.print_resources()
    print("{} total resources found.".format(str(len(course_parser.resources))))
    print("Enter the number corresponding to the resource(s) you wish to download (separated by a space), "
          "or enter '0' to download all resources.")
    print("Example selections: 1 2.1 4.3 6")
    return course_parser


def ask_and_download(course_parser):
    valid = False
    selections = []

    while not valid:
        selections = str(input("Enter selection: ")).split(' ')
        counter = 0
        if '0' in selections:
            break
        for selection in selections:
            if selection not in course_parser.resource_map:
                print("Invalid selection!")
            else:
                counter += 1
        if counter == len(selections):
            valid = True
    moodle_downloader = MoodleResourceDownloader(moodle, course_parser)
    if '0' in selections:
        moodle_downloader.download_all()
    else:
        for selection in selections:
            moodle_downloader.download_mapping(selection)


def main_loop():
    print("Loading courses...")
    course_finder = show_courses()

    try:
        course_number = int(input("Select a course or press enter to exit: ")) - 1
        course_id = course_finder.courses[course_number]['id']
        course_name = course_finder.courses[course_number]['fullname']

        course_parser = show_files(course_name, course_id)

        ask_and_download(course_parser)

    except ValueError:
        print("Exiting")
        sys.exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-host", "--host", help="Hostname (address) of your moodle website")
    parser.add_argument("-u", "--username", help="Username for logging into moodle")
    parser.add_argument("-p", "--password", help="Password for logging into moodle")
    parser.add_argument("-t", "--cookie", help="Existing MoodleSession cookie to use instead of logging in")
    parser.add_argument("-c", "--course", help="Course code to use when downloading")
    parser.add_argument("-d", "--directory", help="directory to use when saving files")
    parser.add_argument("--config", help="Config file to use instead of commandline arguments/interactive mode")
    args = parser.parse_args()

    # 1. Check if config file has been provided.
    if args.config and config_exists(args.config):
        config = load_config_file(args.config)
    # 2. Load a config anyway
    elif config_exists("config.json"):
        config = load_config_file("config.json")
    # 3. No config file, start with empty config and read from input
    else:
        # No config file, manual mode
        config = {
            "host": args.host,
            "username": args.username,
            "password": args.password,
            "cookie": args.cookie,
            "course": args.course,
            "directory": args.directory
        }

    # Now, override any parameters specified by the command line
    if args.host:
        config["host"] = args.host
    if args.username:
        config["username"] = args.username
    if args.password:
        config["password"] = args.password
    if args.cookie:
        config["cookie"] = args.cookie
    if args.course:
        config["course"] = args.course
    if args.directory:
        config["directory"] = args.directory

    # Finally, ask interactively for any missing parameters
    if not config["host"]:
        config["host"] = input("Enter the hostname for your moodle service: ")
    if not config["cookie"] and not config["username"] and not config["password"]:
        result = input("To authenticate using a cookie, type 'y', otherwise press any other key for username/password "
                       "authentication: ")
        if result.lower() == 'y':
            config["cookie"] = input("Paste your MoodleSession cookie: ")

    if not config["username"] and not config["cookie"]:
        config["username"] = input("Enter your moodle username: ")
    if not config["password"] and not config["cookie"]:
        config["password"] = getpass("Enter your moodle password: ")
    if not config["directory"]:
        result = input("Enter a directory to save course content to, or press enter to use the current directory ({})".
                       format(os.getcwd()))
        if result:
            config["directory"] = os.path.abspath(result)
        else:
            config["directory"] = os.getcwd()

    # Create Moodle Instance
    moodle = Moodle(config["host"], config["username"], config["password"], config["cookie"],
                    save_dir=config["directory"])
    if not config["cookie"]:
        try:
            print("Logging in...", end='')
            moodle_authenticator = MoodleAuthenticator(moodle)
            moodle.session = moodle_authenticator.get_session()
        except InvalidLogin:
            print("Error, invalid login")
            sys.exit(1)
    try:
        moodle.get_session_key()
        print('successful')
    except TypeError:
        # Only time this key is null is when a login has failed.
        print("Error, invalid login")
        sys.exit(1)

    while True:
        try:
            main_loop()
        except KeyboardInterrupt:
            print("Exiting...")
            sys.exit(0)
