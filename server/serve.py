import os
import secrets
import sys
from dotenv import load_dotenv
from flask import Flask, render_template, send_from_directory
from flask_httpauth import HTTPBasicAuth
#from ipygis import get_connection_url
from slugify import slugify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import check_password_hash

from forms import AnalysisForm

# test simple import now, convert to module later
sys.path.insert(0, "..")
from models import Analysis

app = Flask(__name__, static_url_path='')
auth = HTTPBasicAuth()
load_dotenv()
allowed_username = os.getenv("USERNAME")
allowed_hash = os.getenv("PASSWORD_HASH")
secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    secret_key = secrets.token_bytes(64)
app.config['SECRET_KEY'] = secret_key

sql_url = f"postgresql://{os.environ.get('PGUSER', 'postgres')}:{os.environ.get('PGPASSWORD', '')}@{os.environ.get('PGHOST', 'localhost')}:{int(os.environ.get('PGPORT', '5432'))}/geoviz"
#sql_url = get_connection_url(dbname="geoviz")
engine = create_engine(sql_url)
session = sessionmaker(bind=engine)()
Analysis.__table__.create(engine, checkfirst=True)


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
        print(form.bbox.data)
        city_name = form.bbox.data
        # analysis = Analysis(
        #     slug = slugify(form.)
        # )
    unfinished_analyses = session.query(Analysis).filter(Analysis.viewed.is_(False)).all()
    if unfinished_analyses:
        running = True
    return render_template(
        'home.html',
        title="Gispo Spatial Analytics",
        description="Import urban datasets and run analyses.",
        form=form,
        running=running,
        analyses=unfinished_analyses
    )


if __name__ == '__main__':
    app.run(threaded=True, port=5000)
