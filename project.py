import sys
import os
from flask import Flask, render_template, g, request, redirect, url_for, flash, jsonify, session, Response
import logging
from sqlalchemy import desc, asc
from werkzeug import secure_filename
import requests
from requests import Session
import json
import cloudinary
import cloudinary.uploader
import cloudinary.api
import datetime
from passlib.hash import sha256_crypt
import stripe
import time
import oauthlib
from threading import Thread


SKETCHFAB_DOMAIN = 'sketchfab.com'
SKETCHFAB_API_URL = 'https://api.{}/v2/models'.format(SKETCHFAB_DOMAIN)
SKETCHFAB_MODEL_URL = 'https://{}/models/'.format(SKETCHFAB_DOMAIN)
OAUTH2_CLIENT_ID = 'YOUR_CLIENT_ID'
USERNAME = 'endorsevr'
PASSWORD = 'Thereisnospoon1'

YOUR_API_TOKEN = "f142a5b017284ab083ba30bfd59247bf"

# App Config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = 'static/uploads/'


# Set allowable MIME Types for upload
ALLOWED_EXTENSIONS = ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip']
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'super secret key'
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL','postgresql://James:james@localhost:5432/mytest')
app.config['SITE'] = "http://0.0.0.0:5000/"
app.config['DEBUG'] = True
app.config['CLIENT_ID'] = "ca_5we9ErQZG1PtAUgdiS9IaOw7RI4J4Sld"
app.config['API_KEY'] = "sk_test_0OzGigpXejNgMJFqJbZWTfgd"
app.config['PUBLISHABLE_KEY'] = "pk_test_JgVPXsrOEQvLo6cP657UUdPQ"
stripe.api_key = "sk_test_0OzGigpXejNgMJFqJbZWTfgd"
cloudinary.config(cloud_name="hdriydpma", api_key="936542698847873", api_secret="URri2QHl0U8e-Q2whUjpqj7I4f8")



# Import crud
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Asset, Base, User, Endorsement, Paragraph, Project

# Create Session
engine = create_engine(SQLALCHEMY_DATABASE_URI)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
db = DBSession()

class Endorse():
    """ This class stores endorsement information."""

    def __init__(self, user, num, endorse):
        self.user = user
        self.num = num
        self.endorse = endorse


def findUser():
    if 'user_id' in session:
        return db.query(User).filter_by(id=session['user_id']).first()
    else:
        return None

def endInfo(user):
    if user:
        if db.query(Endorsement).filter_by(creator_id=user.id).all():
            num = db.query(Endorsement).filter_by(active=True).count()
            endorsements = db.query(Endorsement).filter_by(creator_id=user.id).order_by(desc(Endorsement.time_created)).all()
            this_end = Endorse(user, num, endorsements)
            return this_end
        elif db.query(Endorsement).filter_by(advertiser_id=user.id).all():
            num = db.query(Endorsement).filter_by(active=True).count()
            endorsements = db.query(Endorsement).filter_by(advertiser_id=user.id).order_by(desc(Endorsement.time_created)).all()
            this_end = Endorse(user, num, endorsements)
            return this_end
        else:
            return None
    else:
        return None



# List all assets
@app.route('/')
def index():
    this_user = findUser()
    endorse = endInfo(this_user)
    return render_template('index.html', user=this_user, endorsements=endorse)

@app.route('/endorsements', methods=['GET', 'POST'])
def endorsements():
    this_user = findUser()
    endorse = endInfo(this_user)
    if request.method == 'POST':
        endorse_id = request.form['endorse_id']
        this_asset = db.query(Endorsement).filter_by(id=endorse_id).first()
        this_asset.active = False
        db.add(this_asset)
        db.commit()
        return redirect(url_for('endorsements'))
    return render_template('endorsements.html', user=this_user, endorsements=endorse)

@app.route('/assets')
def assets():
    all_assets = db.query(Asset).order_by(desc(Asset.time_created)).all()
    categories = db.query(Asset.category).group_by(Asset.category).all()
    users = db.query(User).all()
    this_user = findUser()
    endorse = endInfo(this_user)
    return render_template('assets.html', assets=all_assets, user=this_user, users=users, endorsements=endorse,
                           categories=categories)

@app.route('/projects')
def projects():
    all_projects = db.query(Project).order_by(desc(Project.time_created)).all()
    categories = db.query(Project.category).group_by(Project.category).all()
    users = db.query(User).all()
    this_user = findUser()
    endorse = endInfo(this_user)
    return render_template('projects.html', projects=all_projects, user=this_user, users=users, endorsements=endorse,
                           categories=categories)

@app.route('/newest_projects')
def newest_projects():
    all_projects = db.query(Project).order_by(desc(Project.time_created)).all()
    categories = db.query(Project.category).group_by(Project.category).all()
    users = db.query(User).all()
    this_user = findUser()
    endorse = endInfo(this_user)
    return render_template('projects.html', projects=all_projects, user=this_user, users=users, endorsements=endorse,
                           categories=categories)

@app.route('/oldest_projects')
def oldest_projects():
    all_projects = db.query(Project).order_by(asc(Project.time_created)).all()
    categories = db.query(Project.category).group_by(Project.category).all()
    users = db.query(User).all()
    this_user = findUser()
    endorse = endInfo(this_user)
    return render_template('projects.html', projects=all_projects, user=this_user, users=users, endorsements=endorse,
                           categories=categories)

# Sort assets by category
@app.route('/assets/<asset_category>/')
def category(asset_category):
    all_assets = db.query(Asset).filter_by(category=asset_category).order_by(desc(Asset.time_created)).all()
    users = db.query(User).all()
    this_user = findUser()
    endorse = endInfo(this_user)
    return render_template('category.html', assets=all_assets, user=this_user, users=users, category=asset_category,
                           endorsements=endorse)

# Sort assets by category
@app.route('/assets/newest/')
def newest():
    all_assets = db.query(Asset).order_by(desc(Asset.time_created))
    users = db.query(User).all()
    this_user = findUser()
    endorse = endInfo(this_user)
    return render_template('category.html', assets=all_assets, user=this_user, users=users, category='Newest',
                           endorsements=endorse)

@app.route('/assets/oldest/')
def oldest():
    all_assets = db.query(Asset).order_by(asc(Asset.time_created))
    users = db.query(User).all()
    this_user = findUser()
    endorse = endInfo(this_user)
    return render_template('category.html', assets=all_assets, user=this_user, users=users, category='Oldest',
                           endorsements=endorse)

@app.route('/assets/price-high/')
def priceHigh():
    all_assets = db.query(Asset).order_by(desc(Asset.price))
    users = db.query(User).all()
    this_user = findUser()
    endorse = endInfo(this_user)
    return render_template('category.html', assets=all_assets, user=this_user, users=users, category='Price Highest',
                           endorsements=endorse)

@app.route('/assets/price-low/')
def priceLow():
    all_assets = db.query(Asset).order_by(asc(Asset.price))
    users = db.query(User).all()
    this_user = findUser()
    endorse = endInfo(this_user)
    return render_template('category.html', assets=all_assets, user=this_user, users=users, category='Price Lowest',
                           endorsements=endorse)


# Create a new asset
@app.route('/new_project', methods=['GET', 'POST'])
def new_project():
    this_user = findUser()
    endorse = endInfo(this_user)
    if check_auth('new', None):
        if request.method == 'POST':

            this_project = Project(name=request.form['name'], category=request.form['category'], user_id=this_user.id,
                                   time_created=datetime.datetime.now(), tag_line=request.form['tagline'],
                                   website=request.form['website'])

            if request.form['twitch']:
                this_project.twitch = request.form['twitch']
            if request.form['steam']:
                this_project.steam = request.form['steam']
            if request.form['twitter']:
                this_project.twitter = request.form['twitter']

            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename).split(".")
                cloudinary.uploader.upload(request.files['file'], public_id=filename[0])
                this_project.picture_name = filename[0]

            if request.form['youtube']:
                this_url = request.form['youtube']
                split_url = this_url.split("=")
                this_project.youtube_url = split_url[1]

            db.add(this_project)
            db.commit()

            description_text = request.form['description']
            this_text = description_text.split('\n')
            for i in this_text:
                this_paragraph = Paragraph(text=i, project_id=this_project.id, time_created=datetime.datetime.now())
                db.add(this_paragraph)
                db.commit()

            if this_user.website is None:
                this_user.website = this_project.website

            flash("New Project Created", "success")
            if this_project:
                return redirect(url_for('project', project_id=this_project.id))
            else:
                return redirect(url_for('profile'))
        else:
            return render_template('new_project.html', user=this_user, endorsements=endorse)
    else:
        flash("Please Log In", "danger")
        return redirect(url_for('assets'))

# Create a new asset
@app.route('/new_asset', methods=['GET', 'POST'])
def newAsset():
    this_user = findUser()
    endorse = endInfo(this_user)
    if check_auth('new', None):
        user_projects = db.query(Project).filter_by(user_id=session['user_id']).all()
        if this_user.stripe_user_id is None:
            flash("Please setup payment processing", "danger")
            return redirect(url_for('settings'))
        if user_projects:

            if request.method == 'POST':

                file = request.files['file']
                filename = secure_filename(file.filename).split(".")
                cloudinary.uploader.upload(request.files['picture'], public_id=filename[0])
                this_asset = Asset(name=request.form['name'], dimensions=request.form['dimensions'],
                                   category=request.form['category'], sub_category=request.form['subcategory'],
                                   user_id=this_user.id, price=request.form['price'],
                                   time_created=datetime.datetime.now(), tag_line=request.form['tagline'],
                                   project_id=request.form['project'], picture_name=filename[0])

                db.add(this_asset)
                db.commit()

                file = request.files['file']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                    model_file = UPLOAD_FOLDER+filename

                    name = request.form['name']
                    description = request.form['tagline']
                    tags = "endorsevr vr"

                    data = {
                        'token': YOUR_API_TOKEN,
                        'name': name,
                        'description': description,
                        'tags': tags
                    }

                    f = open(model_file, 'rb')

                    files = {
                        'modelFile': f
                    }

                    t = Thread(target=upload, args=(f, this_asset, data, files))
                    t.start()




                flash("New Asset Created", "success")
                if this_asset:
                    return redirect(url_for('asset', asset_id=this_asset.id))
                else:
                    return redirect(url_for('profile'))
            else:
                return render_template('new_asset.html', user=this_user, endorsements=endorse, projects=user_projects)
        else:
            flash("Please create a project first", "danger")
            return redirect(url_for('new_project'))
    else:
        flash("Please Log In", "danger")
        return redirect(url_for('assets'))




# List unique asset
@app.route('/assets/<int:asset_id>/', methods=['GET', 'POST'])
def asset(asset_id):
        this_asset = db.query(Asset).filter_by(id=asset_id).one()
        asset_owner = db.query(User).filter_by(id=this_asset.user_id).one()
        this_project = db.query(Project).filter_by(id=this_asset.project_id).one()
        project_assets = db.query(Asset).filter_by(project_id=this_project.id).all()


        this_user = findUser()
        endorse = endInfo(this_user)
        if request.method == 'POST':
            if request.files['file']:
                    file = request.files['file']
                    filename = secure_filename(file.filename).split(".")
                    cloudinary.uploader.upload(request.files['file'], public_id=filename[0])
                    this_endorsement = Endorsement(advertiser_id=this_user.id, advertiser_username=this_user.username,
                                                   creator_id=asset_owner.id,  creator_username=asset_owner.username,
                                                   texture_file=filename[0], asset_id=this_asset.id,
                                                   asset_name=this_asset.name, asset_picture=this_asset.picture_name,
                                                   time_created=datetime.datetime.now())
                    db.add(this_endorsement)
                    db.commit()
            return redirect(url_for('profile'))

        return render_template('asset.html', asset=this_asset, user=this_user, assetOwner=asset_owner,
                               endorsements=endorse, project=this_project,
                               assets=project_assets, key=app.config['PUBLISHABLE_KEY'])

# List unique asset
@app.route('/projects/<int:project_id>/')
def project(project_id):
        this_project = db.query(Project).filter_by(id=project_id).one()
        asset_owner = db.query(User).filter_by(id=this_project.user_id).one()
        project_assets = db.query(Asset).filter_by(project_id=project_id).all()
        asset_num = db.query(Asset).filter_by(project_id=project_id).count()
        asset_p = db.query(Paragraph).filter_by(project_id=this_project.id).order_by(asc(Paragraph.time_created)).all()
        this_user = findUser()
        endorse = endInfo(this_user)
        return render_template('project.html', project=this_project, user=this_user, assetOwner=asset_owner,
                               endorsements=endorse, description=asset_p, assets=project_assets, asset_num=asset_num)

# Sort assets by category
@app.route('/project/<project_category>/')
def p_category(project_category):
    all_projects = db.query(Project).filter_by(category=project_category).order_by(desc(Project.time_created)).all()
    users = db.query(User).all()
    this_user = findUser()
    endorse = endInfo(this_user)
    return render_template('project_category.html', projects=all_projects, user=this_user, users=users,
                           category=project_category, endorsements=endorse)



# Edit unique asset
@app.route('/assets/<int:asset_id>/edit', methods=['GET', 'POST'])
def editAsset(asset_id):
        this_user = findUser()
        endorse = endInfo(this_user)
        this_asset = db.query(Asset).filter_by(id=asset_id).one()
        user_projects = db.query(Project).filter_by(user_id=session['user_id']).all()
        # Check editing privileges
        if check_auth('asset', asset_id):
            if request.method == 'POST':
                # Check for changing attributes
                file = request.files['file']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                    model_file = UPLOAD_FOLDER+filename

                    name = request.form['name']
                    description = request.form['tagline']
                    tags = "endorsevr vr"

                    data = {
                        'token': YOUR_API_TOKEN,
                        'name': name,
                        'description': description,
                        'tags': tags
                    }

                    f = open(model_file, 'rb')

                    files = {
                        'modelFile': f
                    }

                    try:
                        q = queue.Queue()
                        model_uid = upload(data, files, )
                        this_asset.model_url = model_uid

                    finally:
                        f.close()

                if request.form['name']:
                    this_asset.name = request.form['name']
                if request.form['category']:
                    this_asset.category = request.form['category']
                if request.form['subcategory']:
                    this_asset.sub_category = request.form['subcategory']
                if request.form['project']:
                    this_asset.project_id = request.form['project']
                if request.files['picture']:
                    file = request.files['picture']
                    filename = secure_filename(file.filename).split(".")
                    cloudinary.uploader.upload(request.files['picture'], public_id=filename[0])
                    this_asset.picture_name = filename[0]


                db.add(this_asset)
                db.commit()
                flash("Asset Edited", "success")
                return redirect(url_for('asset',  asset_id=asset_id))
            else:
                return render_template('edit_asset.html', asset=this_asset, user=this_user, endorsements=endorse,
                                       projects=user_projects)
        else:
            flash("Access Denied", "danger")
            return redirect(url_for('asset', asset_id=asset_id))

# Edit unique asset
@app.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
def edit_project(project_id):
        this_user = findUser()
        endorse = endInfo(this_user)
        this_project = db.query(Project).filter_by(id=project_id).one()
        # Check editing privileges
        if check_auth('project', project_id):
            if request.method == 'POST':
                # Check for changing attributes

                if request.form['name']:
                    this_project.name = request.form['name']

                if request.form['category']:
                    this_project.category = request.form['category']
                if request.form['website']:
                    this_project.website = request.form['website']
                if request.form['youtube']:
                    this_url = request.form['youtube']
                    url_split = this_url.split("=")
                    this_project.youtube_url = url_split[1]
                if request.files['file']:
                    file = request.files['file']
                    filename = secure_filename(file.filename).split(".")
                    cloudinary.uploader.upload(request.files['file'], public_id=filename[0])
                    this_project.picture_name = filename[0]
                if request.form['twitch']:
                    this_project.twitch = request.form['twitch']
                if request.form['steam']:
                    this_project.steam = request.form['steam']
                if request.form['twitter']:
                    this_project.twitter = request.form['twitter']

                db.add(this_project)
                db.commit()
                flash("Project Edited", "success")
                return redirect(url_for('project',  project_id=project_id))
            else:
                return render_template('edit_project.html', project=this_project, user=this_user, endorsements=endorse)
        else:
            flash("Access Denied", "danger")
            return redirect(url_for('project', project_id=project_id))

# Delete unique asset
@app.route('/assets/<int:asset_id>/delete/', methods=['GET', 'POST'])
def delete_asset(asset_id):
        if check_auth('asset', asset_id):
            this_asset = db.query(Asset).filter_by(id=asset_id).one()
            db.delete(this_asset)
            db.commit()
            flash("Asset Deleted", "success")
            return redirect(url_for('profile'))
        else:
            flash("Access Denied", "danger")
            return redirect(url_for('asset', asset_id=asset_id))

# Delete unique project
@app.route('/projects/<int:project_id>/delete/', methods=['GET', 'POST'])
def delete_project(project_id):
        if check_auth('project', project_id):
            project_paragraphs = db.query(Paragraph).filter_by(project_id=project_id).all()
            for i in project_paragraphs:
                db.delete(i)
            this_project = db.query(Project).filter_by(id=project_id).one()
            db.delete(this_project)
            db.commit()
            flash("Project Deleted", "success")
            return redirect(url_for('profile'))
        else:
            flash("Access Denied", "danger")
            return redirect(url_for('project', project_id=project_id))

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    this_user = findUser()
    endorse = endInfo(this_user)
    if request.method == 'POST':
        not_unique = db.query(User).filter_by(username=request.form['username']).all()
        if not_unique:
            flash("Register failed, username not unique", "danger")
            return redirect(url_for('index'))
        else:
            hash = sha256_crypt.encrypt(request.form['password'])
            new = User(username=request.form['username'], email=request.form['email'], password_hash=hash)
            db.add(new)
            db.commit()
            session['user_id'] = new.id

            flash("Register and Login Successful", "success")
            return redirect(url_for('projects'))

    return render_template('register.html', user=this_user, endorsements=endorse)


# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    this_user = findUser()
    endorse = endInfo(this_user)
    if this_user:
        return redirect(url_for('profile'))
    if request.method == 'POST':
        this_user = db.query(User).filter_by(username=request.form['username']).first()
        if this_user:
            hash = this_user.password_hash
            if sha256_crypt.verify(request.form['password'], hash):
                session['user_id'] = this_user.id
                flash("Login Successful", "success")
                return redirect(url_for('projects'))
            else:
                flash("Incorrect Username or Password", "danger")
                return redirect(url_for('index'))

        else:
            flash("User does not exist", "danger")
            return redirect(url_for('index'))

    return render_template('login.html', user=this_user, endorsements=endorse)

# Profile page, redirect if not authenticated
@app.route('/profile')
def profile():
    if 'user_id' in session:
        # Find and list all assets created by user
        this_user = findUser()
        endorse = endInfo(this_user)
        user_assets = db.query(Asset).filter_by(user_id=this_user.id).all()
        user_projects = db.query(Project).filter_by(user_id=this_user.id).all()

        return render_template('profile.html', user=this_user, assets=user_assets, endorsements=endorse,
                               projects=user_projects)
    else:
        flash("Please log in", "danger")
        return redirect(url_for('index'))

# Profile page, redirect if not authenticated
@app.route('/user/<int:user_id>/')
def user(user_id):
    this_user = findUser()
    endorse = endInfo(this_user)
    owner = db.query(User).filter_by(id=user_id).first()
    user_projects = db.query(Project).filter_by(user_id=user_id).all()
    user_assets = db.query(Asset).filter_by(user_id=user_id).all()
    return render_template('user.html', user=this_user, this_user=owner, assets=user_assets, endorsements=endorse,
                           projects=user_projects)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
        this_user = findUser()
        endorse = endInfo(this_user)
        stripe_url="https://connect.stripe.com/oauth/authorize?response_type=code&client_id=ca_5we9ErQZG1PtAUgdiS9IaOw7RI4J4Sld&scope=read_write"
        # Check editing privileges
        if check_auth('settings', None):
            if request.method == 'POST':
                # Check for changing attributes
                if request.form['username']:
                    this_user.username = request.form['username']
                if request.form['website']:
                    this_user.website = request.form['website']
                if request.files['file']:
                    file = request.files['file']
                    filename = secure_filename(file.filename).split(".")
                    cloudinary.uploader.upload(request.files['file'], public_id=filename[0])
                    print(filename[0])
                    this_user.profile_pic = filename[0]

                db.add(this_user)
                db.commit()
                flash("Settings Changed", "success")
                return redirect(url_for('profile'))
            else:
                return render_template('settings.html', user=this_user, endorsements=endorse, stripe_url=stripe_url)
        else:
            flash("Please log in", "danger")
            return redirect(url_for('index'))

# Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logged Out", "success")
    return redirect(url_for('projects'))


# Check authentication and editing privileges
def check_auth(content_type, content_id):
    if 'user_id' in session:
        if content_type == 'project':
            this_project = db.query(Project).filter_by(id=content_id).one()
            if this_project.user_id == session['user_id']:
                return True
            else:
                return False

        if content_type == 'asset':
            this_asset = db.query(Asset).filter_by(id=content_id).one()
            if this_asset.user_id == session['user_id']:
                return True
            else:
                return False

        if content_type == 'new':
            return True
        if content_type == 'settings':
            return True
    else:
        return False

# Stripe

@app.route('/authorize')
def authorize():
    stripe_url="https://connect.stripe.com/oauth/authorize?response_type=code&client_id=ca_5we9ErQZG1PtAUgdiS9IaOw7RI4J4Sld&scope=read_write"
    return redirect(stripe_url)

@app.route('/oauth/callback')
def callback():
    this_user = findUser()
    code = request.args.get('code')
    payload = {'grant_type': 'authorization_code', 'client_id': app.config['CLIENT_ID'],
               'client_secret': app.config['API_KEY'], 'code': code}

    # Make /oauth/token endpoint POST request
    url = 'https://connect.stripe.com/oauth/token'
    resp = requests.post(url, params=payload)
    info = json.loads(resp.text)

    this_user.stripe_user_id = info['stripe_user_id']
    this_user.stripe_publishable_key = info['stripe_publishable_key']
    this_user.access_token = info['access_token']
    db.add(this_user)
    db.commit()
    flash("Stripe connected", "success")
    return redirect('settings')

@app.route('/payment/<int:asset_id>/<int:buyer_id>/<int:seller_user_id>/', methods=['GET', 'POST'])
def pay(asset_id, buyer_id, seller_user_id):
    if request.method == 'POST':

        this_asset = db.query(Asset).filter_by(id=asset_id).one()
        price_in_cents = this_asset.price * 100
        price = int(price_in_cents)
        fee = 0.02 * float(price)
        fee = int(fee)
        seller = db.query(User).filter_by(id=seller_user_id).first()
        buyer = db.query(User).filter_by(id=buyer_id).first()
        token = request.form['stripeToken']
        try:
            stripe.Charge.create(amount=price, source=token, currency='usd',
                                 destination=seller.stripe_user_id, application_fee=fee)
            this_endorsement = Endorsement(advertiser_id=buyer.id, advertiser_username=buyer.username,
                                           creator_id=seller.id,  creator_username=seller.username,
                                           asset_id=this_asset.id, asset_name=this_asset.name,
                                           asset_picture=this_asset.picture_name, time_created=datetime.datetime.now())
            db.add(this_endorsement)
            db.commit()
            flash("Payment Successful", "success")
            return redirect(url_for('endorsements'))
        except stripe.CardError:
            flash("Payment Failed", "danger")
            return redirect(url_for('profile'))


# Sketch_up upload

def upload(f, this_asset, data, files):
    """
    Upload a model to sketchfab
    """
    print('Uploading ...')
    tester = Session()

    try:
        r = tester.post(SKETCHFAB_API_URL, data=data, files=files, verify=False)
    except requests.RequestException as e:
        print("An error occured: {}".format(e))
        return

    result = r.json()

    if r.status_code != requests.codes.created:
        print("Upload failed with error: {}".format(result))
        return

    model_uid = result['uid']
    model_url = SKETCHFAB_MODEL_URL + model_uid
    print("Upload successful. Your model is being processed.")
    this_asset.model_url = model_uid
    db.add(this_asset)
    db.commit()
    f.close()


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)