from db import db, User, Course, Assignment, UserToCourse, OfficeHour, UserSavedOfficeHour
from flask import Flask, request
import json

# define db filename
app = Flask(__name__)
db_filename = "cms.db"

# setup config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

# initialize app
db.init_app(app)
with app.app_context():
    db.create_all()


# generalized response formats
def success_response(data, code=200):
    return json.dumps({"success": True, **data}), code

def failure_response(message, code=404):
    return json.dumps({"success": False, "error": message}), code


# -- USER ROUTES --------------------------------------------------

@app.route("/api/users/", methods=["POST"])
def create_user():
    """
    Endpoint for creating a new user
    """
    body = json.loads(request.data)
    name = body.get("name")
    netid = body.get("netid")
    
    if name is None or netid is None:
        return failure_response("Missing one or more required fields (name, netid)!", 400)
    
    new_user = User(name=name, netid=netid)
    db.session.add(new_user)
    db.session.commit()
    return success_response(new_user.serialize(), 201)

@app.route("/api/users/<int:user_id>/")
def get_user(user_id):
    """
    Endpoint for getting a user (includes saved office hours)
    """
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!", 404)
    return success_response(user.serialize())

@app.route("/api/users/<int:user_id>/save_officehour/", methods=["POST"])
def save_office_hour(user_id):
    """
    Endpoint for a user to save a specific office hour slot
    """
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!", 404)
    
    body = json.loads(request.data)
    oh_id = body.get("oh_id")
    
    if oh_id is None:
        return failure_response("Missing required field (oh_id)!", 400)

    office_hour = OfficeHour.query.filter_by(id=oh_id).first()
    if office_hour is None:
        return failure_response("Office hour not found!", 404)
        
    existing_save = UserSavedOfficeHour.query.filter_by(user_id=user_id, oh_id=oh_id).first()
    
    if existing_save:
        return failure_response("Office hour already saved by this user.", 400)

    new_save = UserSavedOfficeHour(user_id=user_id, oh_id=oh_id)
    db.session.add(new_save)
    db.session.commit()
    
    return success_response(user.serialize(), 201)

@app.route("/api/users/<int:user_id>/unsave_officehour/", methods=["POST"])
def unsave_office_hour(user_id):
    """
    Endpoint for a user to unsave a specific office hour slot
    """
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!", 404)
    
    body = json.loads(request.data)
    oh_id = body.get("oh_id")
    
    if oh_id is None:
        return failure_response("Missing required field (oh_id)!", 400)

    saved_oh = UserSavedOfficeHour.query.filter_by(user_id=user_id, oh_id=oh_id).first()
    
    if saved_oh is None:
        return failure_response("Saved office hour not found for this user.", 404)

    db.session.delete(saved_oh)
    db.session.commit()
    
    return success_response(user.serialize())


# -- COURSE ROUTES --------------------------------------------------

@app.route("/api/courses/")
def get_courses():
    """
    Endpoint for getting all courses
    """
    courses = [c.serialize() for c in Course.query.all()]
    return success_response({"courses": courses})

@app.route("/api/courses/", methods=["POST"])
def create_course():
    """
    Endpoint for creating a course
    """
    body = json.loads(request.data)
    code = body.get("code")
    name = body.get("name")
    
    if code is None or name is None:
        return failure_response("Missing one or more required fields (code, name)!", 400)
    
    new_course = Course(code=code, name=name)
    db.session.add(new_course)
    db.session.commit()
    return success_response(new_course.serialize(), 201)

@app.route("/api/courses/<int:course_id>/")
def get_course(course_id):
    """
    Endpoint for getting a course (includes TAs, OH, Assignments)
    """
    course = Course.query.filter_by(id=course_id).first()
    if course is None:
        return failure_response("Course not found!", 404)
    return success_response(course.serialize())

@app.route("/api/courses/<int:course_id>/", methods=["DELETE"])
def delete_course(course_id):
    """
    Endpoint for deleting a course
    """
    course = Course.query.filter_by(id=course_id).first()
    if course is None:
        return failure_response("Course not found!", 404)
    
    data = course.serialize()
    db.session.delete(course)
    db.session.commit()
    return success_response(data)

@app.route("/api/courses/<int:course_id>/add/", methods=["POST"])
def add_user_to_course(course_id):
    """
    Endpoint for adding a user to a course
    """
    course = Course.query.filter_by(id=course_id).first()
    if course is None:
        return failure_response("Course not found!", 404)
    
    body = json.loads(request.data)
    user_id = body.get("user_id")
    user_type = body.get("type")
    
    if user_id is None or user_type is None:
        return failure_response("Missing required fields (user_id, type)!", 400)

    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!", 404)
    
    if user_type not in ["student", "instructor", "TA"]:
        return failure_response("Invalid user type! Must be 'student', 'instructor', or 'TA'.", 400)

    existing_uc = UserToCourse.query.filter_by(user_id=user_id, course_id=course_id).first()
    
    if existing_uc:
        
        if existing_uc.type != user_type:
            existing_uc.type = user_type
        db.session.commit()
    else:
        new_uc = UserToCourse(user_id=user_id, course_id=course_id, type=user_type)
        db.session.add(new_uc)
        db.session.commit()

    return success_response(course.serialize())


# -- ASSIGNMENT ROUTES --------------------------------------------------

@app.route("/api/courses/<int:course_id>/assignment/", methods=["POST"])
def create_assignment(course_id):
    """
    Endpoint for creating a assignment
    """
    course = Course.query.filter_by(id=course_id).first()
    if course is None:
        return failure_response("Course not found!", 404)
    
    body = json.loads(request.data)
    title = body.get("title")
    due_date = body.get("due_date")
    
    if title is None or due_date is None:
        return failure_response("Missing one or more required fields (title, due_date)!", 400)

    try:
        due_date = int(due_date)
    except ValueError:
        return failure_response("Due date must be an integer (UNIX timestamp)!", 400)

    new_assignment = Assignment(title=title, due_date=due_date, course_id=course_id)
    db.session.add(new_assignment)
    db.session.commit()
    return success_response(new_assignment.serialize(), 201)

# -- OFFICE HOUR ROUTES --------------------------------------------------

@app.route("/api/courses/<int:course_id>/officehour/", methods=["POST"])
def create_office_hour(course_id):
    """
    Endpoint for creating an office hour slot for a course.
    Includes validation to ensure ta_id is a TA for the course.
    """
    course = Course.query.filter_by(id=course_id).first()
    if course is None:
        return failure_response("Course not found!", 404)
    
    body = json.loads(request.data)
    day = body.get("day")
    start_time = body.get("start_time")
    end_time = body.get("end_time")
    location = body.get("location")
    ta_id = body.get("ta_id")
    
    if not all([day, start_time, end_time, location, ta_id]):
        return failure_response("Missing one or more required fields (day, start_time, end_time, location, ta_id)!", 400)

    # 1. Check if the TA user exists
    ta = User.query.filter_by(id=ta_id).first()
    if ta is None:
        return failure_response("TA user not found!", 404)
        
    # 2. **NEW VALIDATION: Check if the user is a TA for this course**
    ta_to_course = UserToCourse.query.filter_by(user_id=ta_id, course_id=course_id).first()
    
    if ta_to_course is None or ta_to_course.type != "TA":
        return failure_response("User is not a valid TA for this course!", 403) # Use 403 Forbidden for authorization issues

    new_oh = OfficeHour(
        day=day, 
        start_time=start_time, 
        end_time=end_time,
        location=location,
        course_id=course_id,
        ta_id=ta_id
    )
    
    db.session.add(new_oh)
    db.session.commit()
    return success_response(new_oh.serialize(), 201)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)