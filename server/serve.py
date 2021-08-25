import os
from dotenv import load_dotenv
from flask import Flask
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash


app = Flask(__name__, static_folder='notebooks', static_url_path='')
auth = HTTPBasicAuth()
load_dotenv()
allowed_username = os.getenv("USERNAME")
allowed_hash = os.getenv("PASSWORD_HASH")


@auth.verify_password
def verify_password(username, password):
    if username == allowed_username and \
            check_password_hash(allowed_hash, password):
        return username


@app.route('/map')
@auth.login_required
def map():
    return app.send_static_file('keplergl_map.html')


if __name__ == '__main__':
    app.run(threaded=True, port=5000)
