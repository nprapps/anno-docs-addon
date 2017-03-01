#!/usr/bin/env python

"""
Commands that ease the interaction with the app google spreadsheet
"""
import app_config
import logging
import json
import os
import glob
from fabric.api import task, require
from urllib import urlencode
from utils import prep_bool_arg, check_credentials
from fabric.api import prompt


logging.basicConfig(format=app_config.LOG_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(app_config.LOG_LEVEL)

UPLOAD_URL_TPL = 'https://www.googleapis.com/upload/drive/v2/files'
DRIVE_API_URL = 'https://www.googleapis.com/drive/v2/files'
GS_QUERY_URL = "%s?q=mimeType='application/vnd.google-apps.script'" % (DRIVE_API_URL)
MIMETYPE = 'application/vnd.google-apps.script+json'

EXTS = {
    'js': 'server_js',
    'html': 'html',
}

TYPES = {v: k for k, v in EXTS.items()}


def get_gas_project_id(name, quiet=False):
    """
    gets the project id from the supplied name
    """
    url = "%s and title='%s'" % (GS_QUERY_URL, name)
    kwargs = {
        'credentials': check_credentials(),
        'url': url,
        'method': 'GET'
    }

    resp = send_api_request(kwargs)

    if resp.status == 200:
        return extract_id(resp, quiet=True)
    elif resp.status == 403:
        resp = send_api_request(kwargs, retry=True)
        if resp.status == 200:
            return extract_id(resp)
        else:
            logger.error('Error (%s).' % resp.status)
    else:
        logger.error('Error (%s).' % resp.status)
    return None


def get_folder_id(name):
    """
    gets the project id from the supplied name
    """
    FOLDER_MIME_TYPE = 'application/vnd.google-apps.folder'
    query = "title = '%s' and mimeType = '%s' and '%s' in parents" % (
        name,
        FOLDER_MIME_TYPE,
        app_config.DRIVE_PARENT_FOLDER_ID)

    fields = {
        'q': query,
        'pageSize': 1,
        'spaces': 'drive'
    }
    params = urlencode(fields)
    url = "%s?%s" % (DRIVE_API_URL, params)
    kwargs = {
        'credentials': check_credentials(),
        'url': url,
        'method': 'GET'
    }

    resp = send_api_request(kwargs)

    if resp.status == 200:
        return extract_id(resp)
    elif resp.status == 403:
        resp = send_api_request(kwargs, retry=True)
        if resp.status == 200:
            return extract_id(resp)
        else:
            logger.error('Error (%s).' % resp.status)
    else:
        logger.error('Error (%s).' % resp.status)
    return None


def extract_id(resp, quiet=False):
    """
    extracts the id from the API response
    """
    id = None
    if (len(resp.data['items']) == 0):
        if not quiet:
            logger.error('Project not found. '
                         'Double check the provided name and try again')
    elif (len(resp.data['items']) > 1):
        print len(resp.data['items'])
        logger.error('More than one project in the returned results.'
                     'maybe change the name to be unique?')
    else:
        id = resp.data['items'][0]['id']
    return id


@task(default=True)
def list_projects(owner=None):
    """
    List all the google projects on your drive, pass owner to filter out
    """
    if (owner):
        url = "%s and '%s' in owners" % (GS_QUERY_URL, owner)
    else:
        url = GS_QUERY_URL

    kwargs = {
        'credentials': check_credentials(),
        'url': url,
        'method': 'GET'
    }

    resp = send_api_request(kwargs)

    if resp.status == 200:
        display_list_projects_results(resp)
    elif resp.status == 403:
        resp = send_api_request(kwargs, retry=True)
        if resp.status == 200:
            display_list_projects_results(resp)
        else:
            logger.error('Error (%s).' % resp.status)
    else:
        logger.error('Error (%s).' % resp.status)


def display_list_projects_results(resp):
    """
    display the results of the list projects API
    """
    for f in resp.data['items']:
        for f in resp.data['items']:
            logger.info('Found resource %s id: %s' % (f['title'],
                                                      f['id']))
            logger.info('Download url: %s' % (
                f['exportLinks']['application/vnd.google-apps.script+json']))


@task
def get_project_metadata(name=None, verbose=False):
    """
    Get a google app project metadata, pass the id of the project
    """
    # Parse boolean fabric args
    verbose = prep_bool_arg(verbose)

    name = name if name else app_config.PROJECT_SLUG

    id = get_gas_project_id(name)

    if not id:
        exit()
    url = '%s/%s' % (DRIVE_API_URL, id)

    kwargs = {
        'credentials': check_credentials(),
        'url': url,
        'method': 'GET'
    }

    resp = send_api_request(kwargs)

    if resp.status == 200:
        display_project_metadata_results(resp, verbose)
    elif resp.status == 403:
        resp = send_api_request(kwargs, retry=True)
        if resp.status == 200:
            display_project_metadata_results(resp, verbose)
        else:
            logger.error('Error (%s).' % resp.status)
    else:
        logger.error('Error (%s).' % resp.status)


def display_project_metadata_results(resp, verbose):
    """
    display the results of the project metadata API
    """
    logger.info('Download url: %s' % (
        resp.data['exportLinks']['application/vnd.google-apps.script+json']))
    if (verbose):
        logger.info('File Resource: %s' % (resp.content))


@task
def get_project_files(name=None):
    """
    Get all files in a given google apps script project
    """
    credentials = check_credentials()

    name = name if name else app_config.PROJECT_SLUG

    id = get_gas_project_id(name)

    if not id:
        exit()
    url = '%s/%s' % (DRIVE_API_URL, id)

    kwargs = {
        'credentials': credentials,
        'url': url,
        'method': 'GET'
    }

    resp = send_api_request(kwargs)
    if resp.status == 200:
        url = resp.data['exportLinks'][MIMETYPE]
    elif resp.status == 403:
        resp = send_api_request(kwargs, retry=True)
        if resp.status == 200:
            url = resp.data['exportLinks'][MIMETYPE]
        else:
            logger.error('Error (%s).' % resp.status)
            exit()
    else:
        logger.error('Error (%s).' % resp.status)
        exit()

    if not url:
        logger.error('Did not find download url for %s' % (id))
        exit()

    kwargs = {
        'credentials': credentials,
        'url': url,
        'method': 'GET'
    }

    resp = send_api_request(kwargs)
    if resp.status == 200:
        return get_project_files_results(resp)
    else:
        logger.error('Error (%s).' % resp.status)


def get_project_files_results(resp):
    """
    get the project files API results
    """
    files_found = {}
    for obj in resp.data['files']:
        if obj['type'] == 'server_js':
            ext = 'js'
        elif obj['type'] == 'html':
            ext = 'html'
        else:
            continue
        key = '%s.%s' % (obj['name'], ext)
        files_found[key] = obj
    return files_found


@task
def download(name=None, dest='google_apps_scripts'):
    """
    Download existing project files,
    pass the id of the project and a destination path
    """

    name = name if name else app_config.PROJECT_SLUG
    existing_files = get_project_files(name)
    for k, v in existing_files.iteritems():
        with open('%s/%s' % (dest, k), "w") as f:
            f.write(v['source'])


@task
def upsert(name=None, src='code'):
    """
    Upload project files to drive,
    pass the id of the project and a source path
    """
    require('settings', provided_by=['production', 'development'])

    if not name:
        if app_config.DEPLOYMENT_TARGET == 'production':
            name = app_config.GAS_PROJECT_NAME
        else:
            name = '%s_%s' % (app_config.DEPLOYMENT_TARGET,
                              app_config.GAS_PROJECT_NAME)

    id = get_gas_project_id(name)

    if not id:
        exit()

    existing_files = get_project_files(name)

    files_to_upload = [f for f in glob.glob('%s/*' % src)
                       if f.split('.')[-1] in EXTS.keys()]

    payload = {
        "files": []
    }

    for file_path in files_to_upload:
        key = os.path.basename(file_path)
        file_name, ext = key.split('.')
        try:
            file_type = EXTS[ext]
        except KeyError:
            continue

        try:
            file_to_upload = {
                'id': existing_files[key]['id']
            }
            logger.info(' - Replace %s (id=%s) with %s.' % (
                key,
                existing_files[key]['id'],
                key))
        except KeyError:
            logger.info(' - New file %s found.' % key)
            logger.info("No existing file found for %s." % key)
            file_to_upload = {}

        with open(file_path) as fp:
            file_contents = fp.read()

        file_to_upload.update({
            'name': file_name,
            'type': file_type,
            'source': file_contents
        })

        payload['files'].append(file_to_upload)

    logger.info('Uploading %s files... ' % len(payload['files']))

    # Prepare API request
    kwargs = {
        'credentials': check_credentials(),
        'url': '%s/%s' % (UPLOAD_URL_TPL, id),
        'method': 'PUT',
        'headers': {'Content-Type': 'application/vnd.google-apps.script+json'},
        'body': json.dumps(payload),
    }

    resp = send_api_request(kwargs)

    if resp.status == 200:
        logger.info('Done.')
    else:
        if resp.status == 403:
            resp = send_api_request(kwargs, retry=True)
            if resp.status == 200:
                logger.info('Done.')
                exit()
        logger.error('Error (%s).' % resp.status)


@task
def create(name=None, folderid=None, folder=None, src='code'):
    """
    Create a new google apps script project
    """
    require('settings', provided_by=['production', 'development'])

    if not name:
        if app_config.DEPLOYMENT_TARGET == 'production':
            name = app_config.GAS_PROJECT_NAME
        else:
            name = '%s_%s' % (app_config.DEPLOYMENT_TARGET,
                              app_config.GAS_PROJECT_NAME)

    id = get_gas_project_id(name, quiet=True)

    if id:
        logger.error("Found project with the same name, use upsert to update")
        exit()

    # Get existing project files in drive
    dest_folder_id = None

    files_to_upload = [f for f in glob.glob('%s/*' % src)
                       if f.split('.')[-1] in EXTS.keys()]

    if not folderid:
        if folder:
            dest_folder_id = get_folder_id(folder)
        else:
            dest_folder_id = get_folder_id(app_config.DEPLOYMENT_TARGET)
        if not dest_folder_id:
            logger.error('Did not find the given folder, create it first')
            exit()
        logger.info('folder id: %s' % dest_folder_id)
    else:
        dest_folder_id = folderid

    payload = {
        "files": []
    }

    for file_path in files_to_upload:
        key = os.path.basename(file_path)
        file_name, ext = key.split('.')
        try:
            file_type = EXTS[ext]
        except KeyError:
            continue

        file_to_upload = {}

        with open(file_path) as fp:
            file_contents = fp.read()

        file_to_upload.update({
            'name': file_name,
            'type': file_type,
            'source': file_contents
        })

        payload['files'].append(file_to_upload)

    logger.info('Uploading %s files... ' % len(payload['files']))

    # Prepare API request
    kwargs = {
        'credentials': check_credentials(),
        'url': '%s?convert=true' % (UPLOAD_URL_TPL),
        'method': 'POST',
        'headers': {'Content-Type': 'application/vnd.google-apps.script+json'},
        'body': json.dumps(payload),
    }

    resp = send_api_request(kwargs)

    if resp.status == 200:
        id = resp.data['id']
        if not id:
            logger.error('did not get an id for the new project')
            exit()
        src_folder_id = resp.data['parents'][0]['id']
        success = update_metadata(id, name, src_folder_id, dest_folder_id)
        if success:
            logger.info('Done.')
        else:
            logger.error('Project created but could not update metadata')
    else:
        if resp.status == 403:
            resp = send_api_request(kwargs, retry=True)
            if resp.status == 200:
                logger.info('Done.')
                exit()
        logger.error('Error (%s).' % resp.status)


def update_metadata(id, name, src_folder_id, dest_folder_id):
    """
    update metadata for newly created gas projects
    """

    fields = {
        'removeParents': '%s' % (src_folder_id),
        'addParents': '%s' % (dest_folder_id),
    }
    params = urlencode(fields)
    url = "%s/%s?%s" % (DRIVE_API_URL, id, params)

    # Compose payload
    payload = {
        'title': name,
    }

    kwargs = {
        'credentials': check_credentials(),
        'url': url,
        'method': 'PATCH',
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(payload)
    }

    resp = send_api_request(kwargs)

    if resp.status == 200:
        return True
    return False


def send_api_request(kwargs, retry=False):
    """
    Prompt user for confirmation, erase credentials and reauthenticate
    Returns the authomatic response
    """
    # Refresh the credentials scope and retry
    if retry:
        message = 'Forbidden response. Want to update the credentials & retry?'
        answer = prompt(message, default="No")
        if answer.lower() not in ('y', 'yes', 'buzz off', 'screw you'):
            logger.info('Ok so no retry...bye')
            exit()
        path = os.path.expanduser(app_config.GOOGLE_OAUTH_CREDENTIALS_PATH)
        os.remove(path)
        kwargs['credentials'] = check_credentials()
    logger.debug('API Request: %s ' % kwargs)
    resp = app_config.authomatic.access(**kwargs)
    logger.debug('API Response: %s ' % resp.content)
    return resp
