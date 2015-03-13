import sys
import os
from flask import Flask, render_template, g, request, redirect, url_for, flash, jsonify, session
import logging
from flask.ext.github import GitHub
from werkzeug import secure_filename
import requests
import json
import cloudinary
import cloudinary.uploader
import cloudinary.api

# App Config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = 'static/uploads/'

cloudinary.config(cloud_name="mentorapp", api_key="936542698847873", api_secret="URri2QHl0U8e-Q2whUjpqj7I4f8")

# Set allowable MIME Types for upload
ALLOWED_EXTENSIONS = ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif']
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super secret key'
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['GITHUB_CLIENT_ID'] = '2312fa8eaf712cf786c2'
app.config['GITHUB_CLIENT_SECRET'] = 'ea735a886f5676eb727dd7f8deb64a444997eb7d'

github = GitHub(app)

# Import crud
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Course, Base, CourseItem, User

# Create Session
engine = create_engine('sqlite:///mentor.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
db = DBSession()


# API Endpoints
@app.route('/courses/<int:course_id>/items/JSON')
def CourseJSON(course_id):
    items = db.query(CourseItem).filter_by(course_id=course_id).all()
    return jsonify(courseItems=[i.serialize for i in items])

@app.route('/courses/<int:course_id>/items/<int:item_id>/JSON')
def CourseItemJSON(course_id, item_id):
    thisItem = db.query(CourseItem).filter_by(id=item_id).one()
    return jsonify(Item=[thisItem.serialize])

# List all courses
@app.route('/')
@app.route('/courses')
def courses():
    all_courses = db.query(Course).all()
    users = db.query(User).all()
    if 'user_id' in session:
        this_user = db.query(User).filter_by(id=session['user_id']).first()
    else:
        this_user = None
    return render_template('courses.html', courses=all_courses, user=this_user, users=users)

# Sort courses by category
@app.route('/courses/<course_category>/')
def category(course_category):
    all_courses = db.query(Course).filter_by(category=course_category).all()
    users = db.query(User).all()
    if 'user_id' in session:
        this_user = db.query(User).filter_by(id=session['user_id']).first()
    else:
        this_user = None
    return render_template('category.html', courses=all_courses, user=this_user, users=users)

# Create a new course
@app.route('/new', methods=['GET', 'POST'])
def newCourse():
    if checkAuth('New'):
        this_user = db.query(User).filter_by(id=session['user_id']).first()
        if request.method == 'POST':
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                print(request.files['file'])
                #file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                cloudinary.uploader.upload(request.files['file'], public_id=filename)
                thisCourse = Course(name=request.form['name'], description=request.form['description'],
                                    category=request.form['category'], picture_name=filename, user_id=this_user.id)
            else:
                thisCourse = Course(name=request.form['name'], description=request.form['description'],
                                    category=request.form['category'], user_id=this_user.id)
            db.add(thisCourse)
            db.commit()
            flash("New Course Created", "success")
            return redirect(url_for('courses'))
        else:
            return render_template('new_course.html')
    else:
        flash("Please Log In", "danger")
        return redirect(url_for('courses'))

# List unique course
@app.route('/courses/<int:course_id>/')
def course(course_id):
        this_course = db.query(Course).filter_by(id=course_id).one()
        items = db.query(CourseItem).filter_by(course_id=course_id).all()
        if 'user_id' in session:
            this_user = db.query(User).filter_by(id=session['user_id']).first()
        else:
            this_user = None
        return render_template('course.html', course=this_course, items=items, user=this_user)

# Edit unique course
@app.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
def editCourse(course_id):
        this_course = db.query(Course).filter_by(id=course_id).one()
        old_pic = this_course.picture_name
        # Check editing privileges
        if checkAuth(course_id):
            if request.method == 'POST':
                # Check for changing attributes
                if request.form['name']:
                    this_course.name = request.form['name']
                if request.form['description']:
                    this_course.description = request.form['description']
                if request.form['category']:
                    this_course.category = request.form['category']
                if request.files['file']:
                    # Delete old picture, upload new picture
                    if old_pic:
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], old_pic))
                    file = request.files['file']
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    this_course.picture_name = filename

                db.add(this_course)
                db.commit()
                flash("Course Edited", "success")
                return redirect(url_for('courses'))
            else:
                return render_template('edit.html', course=this_course)
        else:
            flash("Access Denied", "danger")
            return redirect(url_for('courses'))

# Delete unique course
@app.route('/courses/<int:course_id>/deletecourse/', methods=['GET', 'POST'])
def deleteCourse(course_id):
        if checkAuth(course_id):
            this_course = db.query(Course).filter_by(id=course_id).one()
            course_items = db.query(CourseItem).filter_by(course_id=course_id).all()
            for i in course_items:
                db.delete(i)
            db.delete(this_course)
            db.commit()
            flash("Course Deleted", "danger")
            return redirect(url_for('courses'))
        else:
            flash("Access Denied", "danger")
            return redirect(url_for('courses'))

# Create new course item for unique course
@app.route('/courses/<int:course_id>/newitem/', methods=['GET', 'POST'])
def newItem(course_id):
    if checkAuth(course_id):
        this_user = db.query(User).filter_by(id=session['user_id']).first()
        if request.method == 'POST':
            thisItem = None
            # Check for course item media type
            if request.form['videourl']:
                thisUrl = request.form['videourl']
                # Grab youtube ID from url
                referb = thisUrl.split("=")
                thisItem = CourseItem(name=request.form['name'], course_id=course_id, description=request.form['description'],
                                    category=request.form['category'], youtube_url=referb[1], user_id=this_user.id)
            if request.form['audiourl']:
                thisItem = CourseItem(name=request.form['name'], course_id=course_id, description=request.form['description'],
                                    category=request.form['category'], audio_url=request.form['audiourl'],
                                    user_id=this_user.id)
            if request.form['text']:
                thisItem = CourseItem(name=request.form['name'], course_id=course_id, description=request.form['description'],
                                    category=request.form['category'], text=request.form['text'], user_id=this_user.id)
            db.add(thisItem)
            db.commit()
            flash("New Item Created", "success")
            return redirect(url_for('course', course_id=course_id))
        else:
            return render_template('new_item.html', course_id=course_id)
    else:
        flash("Access Denied", "danger")
        return redirect(url_for('courses'))

# Edit course item for unique course
@app.route('/courses/<int:course_id>/<int:item_id>/edititem/', methods=['GET', 'POST'])
def editItem(course_id, item_id):
        this_course = db.query(Course).filter_by(id=course_id).one()
        this_item = db.query(CourseItem).filter_by(id=item_id).one()
        if checkAuth(course_id):
            if request.method == 'POST':
                # Check for changing attributes
                if request.form['name']:
                    this_item.name = request.form['name']
                if request.form['description']:
                    this_item.description = request.form['description']
                if request.form['category']:
                    this_item.category = request.form['category']
                if request.form['videourl']:
                    thisUrl = request.form['videourl']
                    referb = thisUrl.split("=")
                    # Set all media
                    this_item.youtube_url = referb[1]
                    this_item.audio_url = None
                    this_item.text = None
                if request.form['audiourl']:
                    this_item.audio_url = request.form['audiourl']
                    this_item.youtube_url = None
                    this_item.text = None
                if request.form['text']:
                    this_item.text = request.form['text']
                    this_item.audio_url = None
                    this_item.youtube_url = None

                db.add(this_item)
                db.commit()
                flash("Item Edited", "success")
                return redirect(url_for('course', course_id=course_id))
            else:
                return render_template('edit_item.html', course=this_course, item=this_item)
        else:
            flash("Access Denied", "danger")
            return redirect(url_for('courses'))

# Delete course item for unique course
@app.route('/courses/<int:course_id>/<int:item_id>/deleteitem/', methods=['GET', 'POST'])
def deleteItem(course_id, item_id):
        if checkAuth(course_id):
            this_item = db.query(CourseItem).filter_by(id=item_id).one()
            db.delete(this_item)
            db.commit()
            flash("Item Deleted", "danger")
            return redirect(url_for('course', course_id=course_id))
        else:
            flash("Access Denied", "danger")
            return redirect(url_for('courses'))

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
        return redirect(url_for('courses'))

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
    return redirect(url_for('courses'))

# Profile page, redirect if not authenticated
@app.route('/profile')
def profile():
    if 'user_id' in session:
        # Find and list all courses created by user
        this_user = db.query(User).filter_by(id=session['user_id']).first()
        user_courses = db.query(Course).filter_by(user_id=this_user.id).all()
        return render_template('profile.html', user=this_user, courses=user_courses)
    else:
        return redirect(url_for('login'))

# Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logged Out", "success")
    return redirect(url_for('courses'))

# Check authentication and editing privileges
def checkAuth(course_id):
    if 'user_id' in session:
        if course_id == 'New':
            return True
        else:
            this_course = db.query(Course).filter_by(id=course_id).one()
            if this_course.user_id == session['user_id']:
                return True
            else:
                return False
    else:
        return False

if __name__ == '__main__':
    app.debug = True
    app.run()