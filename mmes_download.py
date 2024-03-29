#!/usr/bin/env python3

import os, sys
from subprocess import call, run, CompletedProcess
import shutil
import requests
from requests.auth import HTTPBasicAuth
from progressbar import ProgressBar, Percentage
from datetime import datetime, timedelta
from ftplib import FTP, all_errors

# general variables

now = datetime.now()
one_day_ago = now - timedelta(days=1)
today = now.strftime("%Y%m%d")


# today = '20200909'

# Please make a connection to ftp.arso.gov.si
# Username: Istorms
# Password:  ModelZaOcean18

# download a source  via ftp login

def download_ftp(source, model, tmpdir, filename, filedate=today):
    fileisodate = filedate[0:4] + '-' + filedate[4:6] + '-' + filedate[6:8]
    remotefile = model.filename.format(
                                            currentdate=filedate,
                                            currentisodate=fileisodate,
                                            ext=model.ext
                                )
    remotedir = source.ftp_dir.format(
                    currentdate=filedate,
                    currentisodate=fileisodate,
                    variable=model.variable
    )
    remotepath = model.path.format(
        currentdate=filedate,
        currentisodate=fileisodate,
        variable=model.variable
    )
    filedir = os.path.dirname(filename)
    if not os.path.isdir(filedir):
        os.mkdir(filedir, 0o0775)
    if not os.path.isdir(tmpdir):
        os.mkdir(tmpdir, 0o0775)

    with FTP(source.url) as ftp:
        try:
            # test connection
            # FTP(source.url)
            s = ftp.login(source.username, source.password)
        except all_errors as e:
            print('could not connect to ' + source.url)
            print(e)
            return
        if os.path.isfile(filename):
            print('file ' + filename + '\n already exists skipping')
        else:
            filedir = os.path.dirname(filename)
            if not os.path.isdir(filedir):
                os.mkdir(filedir, 0o0775)
            # remote dir change
            # model dir: sourcedir + modelpath
            changedir = os.path.join(remotedir, remotepath)
            try:
                ftp.cwd(changedir)
                _list = ftp.nlst()
            except:
                print('Remote Dir not found')
                return
            #TODO iterate over subdir in filenames
            # parse list of files in remote dir
            if len(_list)==0:
                msg='Remote dir seems to be empty'
                print(msg)
            for i in _list:
                if str(i).strip().lower() == remotefile.lower():
                    print('Downlading ' + i)
                    dstfile = open(tmpdir + i, 'wb')

                    try:
                        size = ftp.size(i)
                        ftp.retrbinary('RETR ' + i, dstfile.write)
                        print('done')
                    except all_errors as e:
                        print('error on ftp download')
                        print(e)
                        pass
                    try:
                        shutil.copy2(tmpdir + i, filename)
                        print('File copied as ' + filename)
                    except:
                        print('error on copying file')
                    try:
                        os.remove(tmpdir + i)
                        print(tmpdir + i + ' removed')
                    except:
                        print(tmpdir + i + ' not removed')


def download_http(source, model, filename, filedate=today, progress=False):
    """
    Download file from http source with basic authentication
    :rtype: object
    """

    if source.srctype == 'http_login':
        template = model.filename
        fileisodate = filedate[0:4] + '-' + filedate[4:6] + '-' + filedate[6:8]
        remotefile = model.filename.format(
                                              currentdate=filedate,
                                              currentisodate=fileisodate,
                                              ext=model.ext
                                              )

        # basic authentication
        sourceauth = HTTPBasicAuth(source.username, source.password)
        if os.path.isfile(filename): #TODO move check on main script
            print('file ' + filename + ' already exists skipping')
        else:
            filedir = os.path.dirname(filename)
            if not os.path.isdir(filedir):
                os.mkdir(filedir, 0o0775)
            fileurl = source.url + model.path + remotefile
            with requests.get(fileurl, auth=sourceauth, stream=True) as r:
                total_length = r.headers.get('content-length')
                if r.status_code == 200:
                    print('Downloading from ' + fileurl)
                    with open(filename, 'wb') as fd:
                        dl = 0
                        total_length = int(total_length)
                        for chunk in r.iter_content(chunk_size=128):
                            dl += len(chunk)
                            fd.write(chunk)
                            done = int(50 * dl / total_length)
                            if progress:
                                sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (50 - done)))
                                sys.stdout.flush()
                        print('\n')
                else:
                    print(fileurl + ' get a status code of ' + str(r.status_code))


def download_script(scriptdir, source, model, filename, filedate, user="user", passw="passw"):
    if os.path.isfile(filename):
        print('file ' + filename + ' already exists skipping')
    else:
        filedir = os.path.dirname(filename)
        if not os.path.isdir(filedir):
            os.mkdir(filedir, 0o0775)
        script = scriptdir + model.script
        cmd_arguments = [script, filedate, filename, source.username, source.password]
        p = run(cmd_arguments)
