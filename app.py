from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import secrets
import os
import re
from werkzeug import serving

app = Flask(__name__)
if not os.path.isfile('secret.bin'):
    with open('secret.bin', 'wb') as f:
        f.write(secrets.token_bytes(32))
app.secret_key = open('secret.bin', 'rb').read()

def disable_endpoint_logs():
    """Disable logs for requests to specific endpoints."""

    disabled_endpoints = ('/api/events',)

    parent_log_request = serving.WSGIRequestHandler.log_request

    def log_request(self, *args, **kwargs):
        if not any(re.match(f"{de}$", self.path) for de in disabled_endpoints):
            parent_log_request(self, *args, **kwargs)

    serving.WSGIRequestHandler.log_request = log_request

disable_endpoint_logs()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/events')
def get_events():
    return jsonify([])