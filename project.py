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
from flask_oauthlib.client import OAuth
from passlib.hash import sha256_crypt


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

#OAuth
oauth = OAuth(app)

#Twitter
twitter = oauth.remote_app(
    'twitter',
    consumer_key='9JTAk71PnJSxpPOWMz2vrHhWI',
    consumer_secret='n1HPcrUAWeCNJzB2CUkc4j3HaakEEpSIhNKZTxX5QkOBp8R8Id',
    base_url='https://api.twitter.com/1.1/',
    request_token_url='https://api.twitter.com/oauth/request_token',
    access_token_url='https://api.twitter.com/oauth/access_token',
    authorize_url='https://api.twitter.com/oauth/authenticate',
)

#Facebook
facebook = oauth.remote_app(
    'facebook',
    consumer_key='1463359790551415',
    consumer_secret='99ac53adda03bf6b5aba0c56a0f12bfa',
    request_token_params={'scope': 'email'},
    base_url='https://graph.facebook.com',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth'
)


# Import crud
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Asset, Base, User, Endorsement, Paragraph

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
        else:
            return None
    else:
        return None



# List all assets
@app.route('/')
def index():
    this_user = findUser()
    return render_template('index.html', user=this_user)

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
    all_assets = db.query(Asset).all()
    users = db.query(User).all()
    this_user = findUser()
    endorse = endInfo(this_user)
    return render_template('assets.html', assets=all_assets, user=this_user, users=users, endorsements=endorse)

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
@app.route('/new', methods=['GET', 'POST'])
def newAsset():
    this_user = findUser()
    endorse = endInfo(this_user)
    if checkAuth('New'):
        this_user = db.query(User).filter_by(id=session['user_id']).first()
        if request.method == 'POST':

            description_text = request.form['description']
            this_text = description_text.split('\n')

            thisAsset = Asset(name=request.form['name'], dimensions=request.form['dimensions'],
                              category=request.form['category'], sub_category=request.form['subcategory'],
                              user_id=this_user.id, price=request.form['price'], time_created=datetime.datetime.now(),
                              tag_line=request.form['tagline'])

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
            for i in this_text:
                this_paragraph = Paragraph(text=i, asset_id=thisAsset.id, time_created=datetime.datetime.now())
                db.add(this_paragraph)
                db.commit()

            flash("New Asset Created", "success")
            return redirect(url_for('profile'))
        else:
            return render_template('new_asset.html', user=this_user, endorsements=endorse)
    else:
        flash("Please Log In", "danger")
        return redirect(url_for('assets'))

# List unique asset
@app.route('/assets/<int:asset_id>/', methods=['GET', 'POST'])
def asset(asset_id):
        users = db.query(User).all()
        this_asset = db.query(Asset).filter_by(id=asset_id).one()
        asset_owner = db.query(User).filter_by(id=this_asset.user_id).one()
        asset_p = db.query(Paragraph).filter_by(asset_id=this_asset.id).order_by(desc(Paragraph.time_created)).all()
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
                               endorsements=endorse, description=asset_p)

# Edit unique asset
@app.route('/assets/<int:asset_id>/edit', methods=['GET', 'POST'])
def editAsset(asset_id):
        this_user = findUser()
        endorse = endInfo(this_user)
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
                return render_template('edit.html', asset=this_asset, user=this_user, endorsements=endorse)
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

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    this_user = findUser()
    endorse = endInfo(this_user)
    if request.method == 'POST':
        hash = sha256_crypt.encrypt(request.form['password'])
        new = User(username=request.form['username'], email=request.form['email'], password_hash=hash)
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
    if request.method == 'POST':
        this_user = db.query(User).filter_by(username=request.form['username']).first()
        if this_user:
            hash = this_user.password_hash
            if sha256_crypt.verify(request.form['password'], hash):
                session['user_id'] = this_user.id
                flash("Login Successful", "success")
                return redirect(url_for('assets'))

        else:
            flash("User does not exist", "danger")
            return redirect(url_for('assets'))

    return render_template('login.html', user=this_user, endorsements=endorse)

# Profile page, redirect if not authenticated
@app.route('/profile')
def profile():
    if 'user_id' in session:
        # Find and list all assets created by user
        this_user = db.query(User).filter_by(id=session['user_id']).first()
        endorse = endInfo(this_user)
        user_assets = db.query(Asset).filter_by(user_id=this_user.id).all()
        return render_template('profile.html', user=this_user, assets=user_assets, endorsements=endorse)
    else:
        return redirect(url_for('login'))

# Profile page, redirect if not authenticated
@app.route('/user/<int:user_id>/')
def user(user_id):
    this_user = findUser()
    endorse = endInfo(this_user)
    owner = db.query(User).filter_by(id=user_id).first()
    user_assets = db.query(Asset).filter_by(user_id=user_id).all()
    return render_template('user.html', user=this_user, this_user=owner, assets=user_assets, endorsements=endorse)

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

# GithubAuth
@app.route('/github')
def githubauth():
    return github.authorize()

# Auth callback
@app.route('/github-callback')
@github.authorized_handler
def authorized(oauth_token):
    if oauth_token is None:
        flash("Authentication Failed", "danger")
        return redirect(url_for('assets'))

    payload = {'access_token': oauth_token}
    r = requests.get('https://api.github.com/user', params=payload)
    info = json.loads(r.text)
    thisUser = str(info['id'])
    user = db.query(User).filter_by(github_id=thisUser).first()

    if user is None:
        user = User(github_id=info['id'], username=info['login'], profile_pic=info['avatar_url'])
        db.add(user)
        db.commit()

    session['user_id'] = user.id
    flash("Logged In", "success")
    return redirect(url_for('assets'))


#Twitter Auth

@app.route('/twitter')
def twitterAuth():
    callback_url = url_for('oauthorized')
    return twitter.authorize(callback=callback_url)

@twitter.tokengetter
def get_twitter_token():
    if 'twitter_oauth' in session:
        resp = session['twitter_oauth']
        return resp['oauth_token'], resp['oauth_token_secret']

@app.route('/oauthorized')
def oauthorized():
    resp = twitter.authorized_response()

    if resp is None:
        flash("Authentication Failed", "danger")
        return redirect(url_for('assets'))

    session['twitter_oauth'] = resp
    thisuser = str(resp['user_id'])
    user = db.query(User).filter_by(twitter_id=thisuser).first()

    if user is None:
        yes = twitter.request('https://api.twitter.com/1.1/users/show.json?screen_name='+resp['screen_name'])
        photoUrl = yes.data['profile_image_url_https']
        referb = photoUrl.replace("_normal", "")
        user = User(twitter_id=thisuser, username=resp['screen_name'],
                    profile_pic=referb)
        db.add(user)
        db.commit()

    session['user_id'] = user.id
    flash("Logged In", "success")
    return redirect(url_for('assets'))

#Facebook Auth

@app.route('/facebook')
def facebookAuth():
    callback_url = url_for(
        'facebook_authorized',
        next=request.args.get('next') or request.referrer or None,
        _external=True)

    return facebook.authorize(callback=callback_url)

@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')

@app.route('/facebook_authorized')
def facebook_authorized():
    resp = facebook.authorized_response()
    if resp is None:
        flash("Authentication Failed", "danger")
        return redirect(url_for('assets'))

    payload = {'access_token': resp['access_token']}
    r = requests.get('https://graph.facebook.com/me', params=payload)
    info = json.loads(r.text)
    user = db.query(User).filter_by(facebook_id=info['id']).first()
    if user is None:
        user = User(facebook_id=info['id'], username=info['name'],
                    profile_pic='https://graph.facebook.com/'+info['id']+'/picture?type=large')
        db.add(user)
        db.commit()

    session['user_id'] = user.id
    flash("Logged In", "success")
    return redirect(url_for('assets'))


if __name__ == '__main__':
    app.debug = True
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)