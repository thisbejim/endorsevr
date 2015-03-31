import sys
import os
from flask import Flask, render_template, g, request, redirect, url_for, flash, jsonify, session, Response
import logging
from sqlalchemy import desc, asc
from werkzeug import secure_filename
import requests
import json
import cloudinary
import cloudinary.uploader
import cloudinary.api
import datetime
from passlib.hash import sha256_crypt
import stripe
import time

SKETCHFAB_DOMAIN = 'sketchfab.com'
SKETCHFAB_API_URL = 'https://api.{}/v2/models'.format(SKETCHFAB_DOMAIN)
SKETCHFAB_MODEL_URL = 'https://{}/models/'.format(SKETCHFAB_DOMAIN)
OAUTH2_CLIENT_ID = 'YOUR_CLIENT_ID'
USERNAME = 'endorsevr'
PASSWORD = 'Thereisnospoon1'

YOUR_API_TOKEN = "f142a5b017284ab083ba30bfd59247bf"

stripe.api_key = "sk_test_0OzGigpXejNgMJFqJbZWTfgd"
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

cloudinary.config(cloud_name="hdriydpma", api_key="936542698847873", api_secret="URri2QHl0U8e-Q2whUjpqj7I4f8")



# Import crud
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Asset, Base, User, Endorsement, Paragraph, Project, TurnImg

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
    print(categories)
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
    if checkAuth('New'):
        this_user = db.query(User).filter_by(id=session['user_id']).first()
        if request.method == 'POST':

            description_text = request.form['description']
            this_text = description_text.split('\n')

            this_project = Project(name=request.form['name'], category=request.form['category'], user_id=this_user.id,
                                   time_created=datetime.datetime.now(), tag_line=request.form['tagline'])

            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename).split(".")
                cloudinary.uploader.upload(request.files['file'], public_id=filename[0])
                this_project.picture_name = filename[0]

            if request.form['youtube']:
                this_url = request.form['youtube']
                referb = this_url.split("=")
                this_project.youtube_url = referb[1]

            db.add(this_project)
            db.commit()
            for i in this_text:
                this_paragraph = Paragraph(text=i, project_id=this_project.id, time_created=datetime.datetime.now())
                db.add(this_paragraph)
                db.commit()

            flash("New Project Created", "success")
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
    user_projects = db.query(Project).filter_by(user_id=session['user_id']).all()
    endorse = endInfo(this_user)
    if checkAuth('New'):
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

                    try:
                        model_uid = upload(data, files)
                        if poll_processing_status(model_uid)[0] == 1:
                            model = poll_processing_status(model_uid)[1]
                            referb = model.split("models/")
                            this_asset.model_url = referb[1]

                    finally:
                        f.close()

                flash("New Asset Created", "success")
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
        users = db.query(User).all()
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
                               assets=project_assets)

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
        if checkAuth(asset_id):
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
                        model_uid = upload(data, files)
                        if poll_processing_status(model_uid)[0] == 1:
                            model = poll_processing_status(model_uid)[1]
                            split_url = model.split("models/")
                            this_asset.model_url = split_url[1]

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
            return redirect(url_for('assets'))

# Edit unique asset
@app.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
def edit_project(project_id):
        this_user = findUser()
        endorse = endInfo(this_user)
        this_project = db.query(Project).filter_by(id=project_id).one()
        # Check editing privileges
        if True:
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

                db.add(this_project)
                db.commit()
                flash("Project Edited", "success")
                return redirect(url_for('project',  project_id=project_id))
            else:
                return render_template('edit.html', project=this_project, user=this_user, endorsements=endorse)
        else:
            flash("Access Denied", "danger")
            return redirect(url_for('assets'))

# Delete unique asset
@app.route('/assets/<int:asset_id>/delete/', methods=['GET', 'POST'])
def delete_asset(asset_id):
        if checkAuth(asset_id):
            this_asset = db.query(Asset).filter_by(id=asset_id).one()
            db.delete(this_asset)
            db.commit()
            flash("Asset Deleted", "danger")
            return redirect(url_for('profile'))
        else:
            flash("Access Denied", "danger")
            return redirect(url_for('assets'))

# Delete unique project
@app.route('/projects/<int:project_id>/delete/', methods=['GET', 'POST'])
def delete_project(project_id):
        if True:
            this_project = db.query(Project).filter_by(id=project_id).one()
            db.delete(this_project)
            db.commit()
            flash("Project Deleted", "danger")
            return redirect(url_for('profile'))
        else:
            flash("Access Denied", "danger")
            return redirect(url_for('assets'))

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    this_user = findUser()
    endorse = endInfo(this_user)
    if request.method == 'POST':
        not_unique = db.query(User).filter_by(username=request.form['username']).all()
        if not_unique:
            flash("Register failed, username not unique", "danger")
            return redirect(url_for('register'))
        else:
            hash = sha256_crypt.encrypt(request.form['password'])
            new = User(username=request.form['username'], email=request.form['email'], password_hash=hash,
                       advertiser=request.form['inlineRadioOptions'])
            db.add(new)
            db.commit()
            session['user_id'] = new.id

            flash("Register and Login Successful", "success")
            return redirect(url_for('assets'))

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
                return redirect(url_for('assets'))
            else:
                flash("Incorrect Username or Password", "danger")
                return redirect(url_for('login'))

        else:
            flash("User does not exist", "danger")
            return redirect(url_for('login'))

    return render_template('login.html', user=this_user, endorsements=endorse)

# Profile page, redirect if not authenticated
@app.route('/profile')
def profile():
    if 'user_id' in session:
        # Find and list all assets created by user
        this_user = findUser()

        endorse = endInfo(this_user)
        user_assets = db.query(Asset).filter_by(user_id=this_user.id).all()
        projects = db.query(Project).filter_by(user_id=this_user.id).all()

        return render_template('profile.html', user=this_user, assets=user_assets, endorsements=endorse,
                               projects=projects)
    else:
        return redirect(url_for('login'))

# Profile page, redirect if not authenticated
@app.route('/user/<int:user_id>/')
def user(user_id):
    this_user = findUser()
    endorse = endInfo(this_user)
    owner = db.query(User).filter_by(id=user_id).first()
    projects = db.query(Project).filter_by(user_id=user_id).all()
    user_assets = db.query(Asset).filter_by(user_id=user_id).all()
    return render_template('user.html', user=this_user, this_user=owner, assets=user_assets, endorsements=endorse,
                           projects=projects)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
        this_user = findUser()
        endorse = endInfo(this_user)
        # Check editing privileges
        if True:
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
                return render_template('settings.html', user=this_user, endorsements=endorse)

# Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logged Out", "success")
    return redirect(url_for('assets'))



# Check authentication and editing privileges
def checkAuth(asset_id):
    if 'user_id' in session:
        if asset_id == 'New':
            return True
        else:
            this_asset = db.query(Asset).filter_by(id=asset_id).one()
            if this_asset.user_id == session['user_id']:
                return True
            else:
                return False
    else:
        return False

# Stripe

# 3d view

def upload(data, files):
    """
    Upload a model to sketchfab
    """
    print('Uploading ...')

    try:
        r = requests.post(SKETCHFAB_API_URL, data=data, files=files, verify=False)
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
    print("Once the processing is done, the model will be available at: {}".format(model_url))

    return model_uid


def poll_processing_status(model_uid):
    """
    Poll the Sketchfab API to query the processing status
    """
    polling_url = "{}/{}/status?token={}".format(SKETCHFAB_API_URL, model_uid, YOUR_API_TOKEN)
    max_errors = 10
    errors = 0
    retry = 0
    max_retries = 50
    retry_timeout = 5  # seconds

    print("Start polling processing status for model {}".format(model_uid))

    while (retry < max_retries) and (errors < max_errors):
        print("Try polling processing status (attempt #{}) ...".format(retry))

        try:
            r = requests.get(polling_url)
        except requests.RequestException as e:
            print("Try failed with error {}".format(e))
            errors += 1
            retry += 1
            continue

        result = r.json()

        if r.status_code != requests.codes.ok:
            print("Upload failed with error: {}".format(result['error']))
            errors += 1
            retry += 1
            continue

        processing_status = result['processing']
        if processing_status == 'PENDING':
            print("Your model is in the processing queue. Will retry in {} seconds".format(retry_timeout))
            print("Want to skip the line? Get a pro account! https://sketchfab.com/plans")
            retry += 1
            time.sleep(retry_timeout)
            continue
        elif processing_status == 'PROCESSING':
            print("Your model is still being processed. Will retry in {} seconds".format(retry_timeout))
            retry += 1
            time.sleep(retry_timeout)
            continue
        elif processing_status == 'FAILED':
            print("Processing failed: {}".format(result['error']))
            return
        elif processing_status == 'SUCCEEDED':
            model_url = SKETCHFAB_MODEL_URL + model_uid
            this = [1, model_url]
            print("Processing successful. Check your model here: {}".format(model_url))
            return this

        retry += 1

    print("Stopped polling after too many retries or too many errors")


if __name__ == '__main__':
    app.debug = True
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)