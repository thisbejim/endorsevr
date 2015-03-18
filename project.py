import sys
import os
from flask import Flask, render_template, g, request, redirect, url_for, flash, jsonify, session
import logging
from sqlalchemy import desc, asc
from flask.ext.github import GitHub
from werkzeug import secure_filename
import requests
import json
import cloudinary
import cloudinary.uploader
import cloudinary.api
import datetime


# App Config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = 'static/uploads/'

# Set allowable MIME Types for upload
ALLOWED_EXTENSIONS = ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif']
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super secret key'
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL','postgresql://James:james@localhost:5432/mytest')
app.config['GITHUB_CLIENT_ID'] = '2312fa8eaf712cf786c2'
app.config['GITHUB_CLIENT_SECRET'] = 'ea735a886f5676eb727dd7f8deb64a444997eb7d'

cloudinary.config(cloud_name="hdriydpma", api_key="936542698847873", api_secret="URri2QHl0U8e-Q2whUjpqj7I4f8")

github = GitHub(app)

# Import crud
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Asset, Base, User

# Create Session
engine = create_engine(SQLALCHEMY_DATABASE_URI)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
db = DBSession()


# List all assets
@app.route('/')
def index():
    if 'user_id' in session:
        this_user = db.query(User).filter_by(id=session['user_id']).first()
    else:
        this_user = None
    return render_template('index.html', user=this_user)

@app.route('/assets')
def assets():
    all_assets = db.query(Asset).order_by(desc(Asset.time_created)).all()
    users = db.query(User).all()
    if 'user_id' in session:
        this_user = db.query(User).filter_by(id=session['user_id']).first()
    else:
        this_user = None
    return render_template('assets.html', assets=all_assets, user=this_user, users=users)

# Sort assets by category
@app.route('/assets/<asset_category>/')
def category(asset_category):
    all_assets = db.query(Asset).filter_by(category=asset_category).order_by(desc(Asset.time_created)).all()
    users = db.query(User).all()
    if 'user_id' in session:
        this_user = db.query(User).filter_by(id=session['user_id']).first()
    else:
        this_user = None
    return render_template('category.html', assets=all_assets, user=this_user, users=users, category=asset_category)

# Sort assets by category
@app.route('/assets/newest/')
def newest():
    all_assets = db.query(Asset).order_by(desc(Asset.time_created))
    users = db.query(User).all()
    if 'user_id' in session:
        this_user = db.query(User).filter_by(id=session['user_id']).first()
    else:
        this_user = None
    return render_template('category.html', assets=all_assets, user=this_user, users=users)

@app.route('/assets/oldest/')
def oldest():
    all_assets = db.query(Asset).order_by(asc(Asset.time_created))
    users = db.query(User).all()
    if 'user_id' in session:
        this_user = db.query(User).filter_by(id=session['user_id']).first()
    else:
        this_user = None
    return render_template('category.html', assets=all_assets, user=this_user, users=users)

@app.route('/assets/price-high/')
def priceHigh():
    all_assets = db.query(Asset).order_by(desc(Asset.price))
    users = db.query(User).all()
    if 'user_id' in session:
        this_user = db.query(User).filter_by(id=session['user_id']).first()
    else:
        this_user = None
    return render_template('category.html', assets=all_assets, user=this_user, users=users)

@app.route('/assets/price-low/')
def priceLow():
    all_assets = db.query(Asset).order_by(asc(Asset.price))
    users = db.query(User).all()
    if 'user_id' in session:
        this_user = db.query(User).filter_by(id=session['user_id']).first()
    else:
        this_user = None
    return render_template('category.html', assets=all_assets, user=this_user, users=users)

# Create a new asset
@app.route('/new', methods=['GET', 'POST'])
def newAsset():
    if 'user_id' in session:
        this_user = db.query(User).filter_by(id=session['user_id']).first()
    else:
        this_user = None
    if checkAuth('New'):
        this_user = db.query(User).filter_by(id=session['user_id']).first()
        if request.method == 'POST':
            thisAsset = Asset(name=request.form['name'], dimensions=request.form['dimensions'],
                              description=request.form['description'], category=request.form['category'],
                              user_id=this_user.id, price=request.form['price'], time_created=datetime.datetime.now(),
                              tagline=request.form['tagline'])

            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename).split(".")
                cloudinary.uploader.upload(request.files['file'], public_id=filename[0])
                thisAsset.picture_name = filename[0]

            if request.form['youtube']:
                thisUrl = request.form['youtube']
                referb = thisUrl.split("=")
                thisAsset.youtube_url = referb[1]

            db.add(thisAsset)
            db.commit()
            flash("New Asset Created", "success")
            return redirect(url_for('profile'))
        else:
            return render_template('new_asset.html', user=this_user)
    else:
        flash("Please Log In", "danger")
        return redirect(url_for('assets'))

# List unique asset
@app.route('/assets/<int:asset_id>/')
def asset(asset_id):
        users = db.query(User).all()
        this_asset = db.query(Asset).filter_by(id=asset_id).one()
        asset_owner = db.query(User).filter_by(id=this_asset.user_id).one()
        if 'user_id' in session:
            this_user = db.query(User).filter_by(id=session['user_id']).first()
        else:
            this_user = None
        return render_template('asset.html', asset=this_asset, user=this_user, assetOwner=asset_owner)

# Edit unique asset
@app.route('/assets/<int:asset_id>/edit', methods=['GET', 'POST'])
def editAsset(asset_id):
        if 'user_id' in session:
            this_user = db.query(User).filter_by(id=session['user_id']).first()
        else:
            this_user = None
        this_asset = db.query(Asset).filter_by(id=asset_id).one()
        # Check editing privileges
        if checkAuth(asset_id):
            if request.method == 'POST':
                # Check for changing attributes
                if request.form['name']:
                    this_asset.name = request.form['name']
                if request.form['description']:
                    this_asset.description = request.form['description']
                if request.form['category']:
                    this_asset.category = request.form['category']
                if request.files['file']:
                    file = request.files['file']
                    filename = secure_filename(file.filename).split(".")
                    cloudinary.uploader.upload(request.files['file'], public_id=filename[0])
                    this_asset.picture_name = filename[0]
                if request.form['youtube']:
                    thisUrl = request.form['youtube']
                    referb = thisUrl.split("=")
                    this_asset.youtube_url = referb[1]

                db.add(this_asset)
                db.commit()
                flash("Asset Edited", "success")
                return redirect(url_for('profile'))
            else:
                return render_template('edit.html', asset=this_asset, user=this_user)
        else:
            flash("Access Denied", "danger")
            return redirect(url_for('assets'))

# Delete unique asset
@app.route('/assets/<int:asset_id>/deleteasset/', methods=['GET', 'POST'])
def deleteAsset(asset_id):
        if checkAuth(asset_id):
            this_asset = db.query(Asset).filter_by(id=asset_id).one()
            db.delete(this_asset)
            db.commit()
            flash("Asset Deleted", "danger")
            return redirect(url_for('profile'))
        else:
            flash("Access Denied", "danger")
            return redirect(url_for('assets'))

# Login
@app.route('/login')
def login():
    return github.authorize()

# Auth callback
@app.route('/github-callback')
@github.authorized_handler
def authorized(oauth_token):
    if oauth_token is None:
        flash("Authentication Failed", "danger")
        return redirect(url_for('assets'))

    user = db.query(User).filter_by(github_access_token=oauth_token).first()
    # If user doesn't exist, create new user
    if user is None:
        payload = {'access_token': oauth_token}
        r = requests.get('https://api.github.com/user', params=payload)
        info = json.loads(r.text)
        user = User(github_access_token=oauth_token, username=info['login'], profile_pic=info['avatar_url'])
        db.add(user)
        db.commit()

    session['user_id'] = user.id
    flash("Logged In", "success")
    return redirect(url_for('assets'))

# Profile page, redirect if not authenticated
@app.route('/profile')
def profile():
    if 'user_id' in session:
        # Find and list all assets created by user
        this_user = db.query(User).filter_by(id=session['user_id']).first()
        user_assets = db.query(Asset).filter_by(user_id=this_user.id).all()
        return render_template('profile.html', user=this_user, assets=user_assets)
    else:
        return redirect(url_for('login'))

# Profile page, redirect if not authenticated
@app.route('/user/<int:user_id>/')
def user(user_id):
    if 'user_id' in session:
        # Find and list all assets created by user
        this_user = db.query(User).filter_by(id=session['user_id']).first()
    else:
        this_user = None
    owner = db.query(User).filter_by(id=user_id).first()
    user_assets = db.query(Asset).filter_by(user_id=user_id).all()
    return render_template('user.html', user=owner, this_user=this_user, assets=user_assets)


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

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)