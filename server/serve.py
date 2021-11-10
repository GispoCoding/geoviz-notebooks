import os
import secrets
import subprocess
import sys
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, send_from_directory
from flask_httpauth import HTTPBasicAuth
from geoalchemy2.shape import from_shape
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


# retain this for now to allow access to old public schema map
@app.route('/map')
@auth.login_required
def map():
    return send_from_directory('notebooks', 'keplergl_map.html')


@app.route('/maps/')
@auth.login_required
def maps():
    analyses = session.query(Analysis).all()
    return render_template(
        'maps.html',
        title="Result maps",
        analyses=analyses
    )


@app.route('/maps/<string:slug>')
@auth.login_required
def map_for_city(slug):
    # mark map viewed to remove it from front page
    analysis = session.query(Analysis).filter(Analysis.slug == slug).first()
    analysis.viewed = True
    session.commit()
    return send_from_directory('maps', f'{slug}.html')


# no login needed, this is open source code
@app.route('/static/<string:file>')
def send_static_file(file):
    return send_from_directory('static', file)


@app.route('/', methods=["GET", "POST"])
@auth.login_required
def home():
    # our fancy UI
    form = AnalysisForm()
    if form.validate_on_submit():
        city_name = form.bbox.form.city.data
        gtfs_url = form.gtfs_url.data
        bbox_string = " ".join(form.bbox.form.bbox.data.split(","))
        dataset_string = " ".join(form.dataset_selection.data)
        # this should be safe, as shell injections are not possible with Popen
        # and Flask has sanitized the field inputs?
        process = subprocess.Popen([
            "../import.py",
            city_name,
            "--datasets",
            dataset_string,
            "--bbox",
            bbox_string,
            "--gtfs",
            gtfs_url,
            "--export"
        ])
        # TODO: wait 0.1 before redirect to display analysis to the user?
        return redirect('/')
    unviewed_analyses = session.query(Analysis).filter(Analysis.viewed.is_(False)).all()
    running_analyses = session.query(Analysis).filter(Analysis.finish_time.is_(None)).all()

    print(form.errors)
    return render_template(
        'home.html',
        title="Gispo Spatial Analytics",
        description="Import urban datasets and run analyses.",
        form=form,
        running=running_analyses,
        analyses=unviewed_analyses
    )


if __name__ == '__main__':
    app.run(threaded=True, port=5000)
