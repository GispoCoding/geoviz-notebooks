import os
import secrets
from dotenv import load_dotenv
from flask import Flask, render_template, send_from_directory
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash

from forms import AnalysisForm


app = Flask(__name__, static_url_path='')
auth = HTTPBasicAuth()
load_dotenv()
allowed_username = os.getenv("USERNAME")
allowed_hash = os.getenv("PASSWORD_HASH")
secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    secret_key = secrets.token_bytes(64)
app.config['SECRET_KEY'] = secret_key


@auth.verify_password
def verify_password(username, password):
    if username == allowed_username and \
            check_password_hash(allowed_hash, password):
        return username


@app.route('/map')
@auth.login_required
def map():
    return send_from_directory('notebooks', 'keplergl_map.html')


@app.route('/static/<string:file>')
def send_static_file(file):
    return send_from_directory('static', file)


@app.route('/', methods=["GET", "POST"])
@auth.login_required
def home():
    # our fancy UI
    running = False
    form = AnalysisForm()
    if form.validate_on_submit():
        running = True
    return render_template(
        'home.html',
        title="Gispo Spatial Analytics",
        description="Import urban datasets and run analyses.",
        form=form,
        running=running
    )


if __name__ == '__main__':
    app.run(threaded=True, port=5000)
