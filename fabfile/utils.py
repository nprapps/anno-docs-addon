#!/usr/bin/env python

import app_config
import subprocess
import os
import webbrowser
import logging

from distutils.util import strtobool
from distutils.spawn import find_executable
from fabric.api import prompt
from oauth import get_credentials
from time import sleep

logging.basicConfig(format=app_config.LOG_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(app_config.LOG_LEVEL)

"""
Utilities used by multiple commands.
"""


def confirm(message):
    """
    Verify a users intentions.
    """
    answer = prompt(message, default="Not at all")

    if answer.lower() not in ('y', 'yes', 'buzz off', 'screw you'):
        exit()


def prep_bool_arg(arg):
    return bool(strtobool(str(arg)))


def check_credentials():
    """
    Check credentials and spawn server and browser if not
    """
    credentials = get_credentials()
    if not credentials:
        try:
            with open(os.devnull, 'w') as fnull:
                logger.info('Credentials were not found or permissions were not correct. Automatically opening a browser to authenticate with Google.')
                gunicorn = find_executable('gunicorn')
                process = subprocess.Popen([gunicorn, '-b', '127.0.0.1:8888', 'app:wsgi_app'], stdout=fnull, stderr=fnull)
                webbrowser.open_new('http://127.0.0.1:8888/oauth')
                logger.info('Waiting...')
                while not credentials:
                    try:
                        credentials = get_credentials()
                        sleep(1)
                    except ValueError:
                        continue
                logger.info('Successfully authenticated!')
                process.terminate()
        except KeyboardInterrupt:
            logger.info('\nCtrl-c pressed. Later, skater!')
            exit()
    return credentials
