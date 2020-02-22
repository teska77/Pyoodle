# Pyoodle
A utility for interactively downloading course content from any moodle instance!

## Getting Started
This program relies on two libraries, *requests* and *bs4*, ensure you have these installed as well as
Python 3.7 or later.

To run, either execute the script directly, or launch using Python:
```shell script
python3 pyoodle.py <options>
```
By default, if no configuration file is found, no config is provided, and no arguments are provided - the script will
ask you for interactively for your details.

These details can be provided in the means of arguments, or a config file - they are:

| Flag              | Purpose                                       |
| ----------------- | --------------------------------------------- |
| -h, --host        | Hostname of your moodle instance (URL)        |
| -u, --username    | Username to log into moodle with *(not required if using cookie authentication)* |
| -p, --password    | Password to log into moodle with *(not required if using cookie authentication)* |
| -t, --cookie      | *MoodleSession* cookie from authenticated session *(not required if using login authentication)*  |
| -d, --directory   | Directory to use when saving course content   |
| -c, --course      | **Not yet implemented** Course code to auto download from |
| --config          | Path pointing to config file to load settings from |

These options can also be provided in a config file, example:

**config.json**
```json
{
  "username": "abcd123",
  "host": "https://moodle.myuniversity.ac.uk",
  "directory" : "."
}
```