from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
app = Flask(__name__)

#import crud
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Course, Base, CourseItem

#Create Session
engine = create_engine('sqlite:///mentor.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/')
@app.route('/courses')
def courses():
    all_courses = session.query(Course).all()
    return render_template('courses.html', courses=all_courses)

@app.route('/new', methods=['GET', 'POST'])
def newCourse():
    if request.method == 'POST':
        thisCourse = Course(name=request.form['name'], description=request.form['description'],
                            category=request.form['category'], timezone=request.form['timezone'],
                            max_students=request.form['maxstudents'])
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
        thisItem = CourseItem(name=request.form['name'], course_id=course_id, description=request.form['description'],
                              category=request.form['category'])
        session.add(thisItem)
        session.commit()
        flash("New Item Created")
        return redirect(url_for('course', course_id=course_id))
    else:
        return render_template('new_item.html', course_id=course_id)



if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)