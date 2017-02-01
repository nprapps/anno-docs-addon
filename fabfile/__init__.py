#!/usr/bin/env python
# _*_ coding:utf-8 _*_
from fabric.api import local, task
from fabric.state import env

import app_config
# Other fabfiles
import gs
import logging

logging.basicConfig(format=app_config.LOG_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(app_config.LOG_LEVEL)

"""
Environments

Changing environment requires a full-stack test.
An environment points to both a server and an S3
bucket.
"""


@task
def production():
    """
    Run as though on production.
    """
    env.settings = 'production'
    app_config.configure_targets(env.settings)


@task
def development():
    """
    Run as though on development.
    """
    env.settings = 'development'
    app_config.configure_targets(env.settings)


@task
def app(port='8000'):
    """
    Serve app.py.
    """

    if env.get('settings'):
        local("DEPLOYMENT_TARGET=%s bash -c 'gunicorn -b 0.0.0.0:%s --timeout 3600 --reload --log-file=logs/app.log app:wsgi_app'" % (env.settings, port))
    else:
        local('gunicorn -b 0.0.0.0:%s --timeout 3600 --reload --log-file=logs/app.log app:wsgi_app' % port)


@task(default=True)
def list():
    """
    Execute list as default fab command
    """
    local('fab -l')
