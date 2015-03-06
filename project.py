import sys
import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask.ext.github import GitHub
from werkzeug import secure_filename

UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif']

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['GITHUB_CLIENT_ID'] = None
app.config['GITHUB_CLIENT_SECRET'] = None

github = GitHub(app)

#import crud
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Course, Base, CourseItem, User

#Create Session
engine = create_engine('sqlite:///mentor.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/')
@app.route('/courses')
def courses():
    all_courses = session.query(Course).all()
    return render_template('courses.html', courses=all_courses)

@app.route('/new', methods=['GET', 'POST'])
def newCourse():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            thisCourse = Course(name=request.form['name'], description=request.form['description'],
                                category=request.form['category'], picture_name=filename)
        else:
            thisCourse = Course(name=request.form['name'], description=request.form['description'],
                                category=request.form['category'])
        session.add(thisCourse)
        session.commit()
        flash("New Course Created")
        return redirect(url_for('courses'))
    else:
        return render_template('new_course.html')

@app.route('/courses/<int:course_id>/')
def course(course_id):
        this_course = session.query(Course).filter_by(id=course_id).one()
        items = session.query(CourseItem).filter_by(course_id=course_id).all()
        return render_template('course.html', course=this_course, items=items)

@app.route('/courses/<int:course_id>/newitem/', methods=['GET', 'POST'])
def newItem(course_id):
    if request.method == 'POST':
        thisItem = None
        if request.form['videourl']:
            thisUrl = request.form['videourl']
            referb = thisUrl.split("=")
            thisItem = CourseItem(name=request.form['name'], course_id=course_id, description=request.form['description'],
                                  category=request.form['category'], youtube_url=referb[1])
        if request.form['audiourl']:
            thisItem = CourseItem(name=request.form['name'], course_id=course_id, description=request.form['description'],
                                  category=request.form['category'], audio_url=request.form['audiourl'])
        if request.form['text']:
            thisItem = CourseItem(name=request.form['name'], course_id=course_id, description=request.form['description'],
                                  category=request.form['category'], text=request.form['text'])
        session.add(thisItem)
        session.commit()
        flash("New Item Created")
        return redirect(url_for('course', course_id=course_id))
    else:
        return render_template('new_item.html', course_id=course_id)

@app.route('/login')
def login():
    return github.authorize()

@app.route('/github-callback')
@github.authorized_handler
def authorized(oauth_token):
    next_url = request.args.get('next') or url_for('index')
    if oauth_token is None:
        flash("Authorization failed.")
        return redirect(next_url)

    user = User.query.filter_by(github_access_token=oauth_token).first()
    if user is None:
        user = User(oauth_token)
        session.add(user)

    user.github_access_token = oauth_token
    session.commit()
    return redirect(next_url)

@github.access_token_getter
def token_getter():
    user = g.user
    if user is not None:
        return user.github_access_token

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)