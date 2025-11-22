from db import db, User, Course, Assignment, UserToCourse
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
    Endpoint for getting a user
    """
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!", 404)
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
    Endpoint for getting a course
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
    
    if user_type not in ["student", "instructor"]:
        return failure_response("Invalid user type!", 400)

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)