#!/usr/bin/env python

import json
import os
import threading
import time

import requests
from flask import Flask, render_template, redirect, url_for, request, flash

class FileInfo(object):
    def __init__(self, owner, name):
        self.owner = owner
        self.name = name
        self.cached = False

basedir = os.path.dirname(os.path.realpath(__file__))
cache_dir = os.path.join(basedir, 'cache')

shared = {}
finished_transfers = {}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'

def request_upload(host, filename):
    requests.get('http://' + host + ':12345', params=json.dumps({'file': filename}))
    print '[INFO] Upload request sent to {0}'.format(host)

def handle_upload(data, uploader_ip, filename):
    path = os.path.join(cache_dir, filename)
    with open(path, 'wb+') as f:
        f.write(data)
    print '[INFO] {0} was uploaded'.format(filename)
    fileinfos = shared.get(uploader_ip)
    if fileinfos:
        for fileinfo in fileinfos:
            if fileinfo.name == filename:
                fileinfo.cached = True

def handle_download(_download_request):
    downloader = _download_request[0]
    filename = _download_request[1]
    path = os.path.join(cache_dir, filename)
    success = False
    while not success:
        if os.path.exists(path):
            size = str(os.path.getsize(path))
            with open(path, 'rb') as f:
                response = requests.post('http://' + downloader + ':12345',\
                    headers={'Content-Length': size}, params={'filename': filename}, files={'file': f})
                print '[INFO] {0} was downloaded by {1}'.format(filename, downloader)
                if response.status_code == 200:
                    success = True
                    global finished_transfers
                    if downloader not in finished_transfers.iterkeys():
                        finished_transfers[downloader] = []
                    finished_transfers[downloader].append(filename)
        else:
            time.sleep(1)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html.j2', shared=shared)

@app.route('/finished_transfers', methods=['GET'])
def flash_finished_transfers():
    client_ip = request.remote_addr
    if client_ip in finished_transfers.iterkeys():
        for _file in finished_transfers[client_ip]:
            filename = os.path.split(os.path.splitdrive(_file)[1])[1]
            flash('File transfer has finished: {0}'.format(filename), 'success')
        finished_transfers[client_ip] = []
    return render_template('flashes.html.j2')

@app.route('/cache_info', methods=['GET'])
def cache_info():
    return json.dumps({'cached': os.listdir(cache_dir)})

@app.route('/download/<host>/<filename>', methods=['GET'])
def download(host, filename):
    path_in_cache = os.path.join(cache_dir, filename)
    if os.path.exists(path_in_cache):
        print '[INFO] {0} is cached'.format(filename)
    else:
        upload_thread = threading.Thread(target=request_upload, args=(host, filename,))
        upload_thread.start()
    downloader = request.remote_addr
    _download_request = (downloader, filename)
    download_thread = threading.Thread(target=handle_download, args=(_download_request,))
    download_thread.start()
    flash('File transfer has started: {0}'.format(filename), 'notification')
    return redirect(url_for('index'))

@app.route('/advertise', methods=['POST'])
def advertise():
    owner_ip = request.remote_addr
    owner = request.args.get('owner')
    filenames = json.loads(request.args.get('shared'))
    shared[request.remote_addr] = [FileInfo(owner, filename) for filename in filenames]
    return '', 200

@app.route('/upload', methods=['POST'])
def upload():
    uploader_ip = request.remote_addr
    filename = request.args.get('filename')
    data = request.get_data()
    thread = threading.Thread(target=handle_upload, args=(data, uploader_ip, filename,))
    thread.start()
    return '', 200

app.run(debug=True)
