from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class UserToCourse(db.Model):
    """
    Task model
    one-to-many relatinoship with Subtask model
    many-many relationship with Category model
    """
    __tablename__ = "user_to_course"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    type = db.Column(db.String, nullable=False)
    
    user = db.relationship("User", back_populates="courses_in_user")
    course = db.relationship("Course", back_populates="users_in_course")

    def serialize_course_in_user(self):
        """
        Seralize a user's course object
        """
        return self.course.serialize_user_course()


class User(db.Model):
    """
    User model
    """
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    netid = db.Column(db.String, nullable=False)
    
    courses_in_user = db.relationship("UserToCourse", back_populates="user", cascade="all, delete")

    def serialize(self):
        """
        Seralize a user object
        """
        return {
            "id": self.id,
            "name": self.name,
            "netid": self.netid,
            "courses": [c.serialize_course_in_user() for c in self.courses_in_user]
        }

    def serialize_course_user(self):
        """
        Seralize a user in a course object
        """
        return {
            "id": self.id,
            "name": self.name,
            "netid": self.netid,
            "courses": None  # Exclude deep course data
        }

class Course(db.Model):
    """
    Course model
    """
    __tablename__ = "course"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    
    assignments = db.relationship("Assignment", cascade="all, delete")
    users_in_course = db.relationship("UserToCourse", back_populates="course", cascade="all, delete")

    def serialize(self):
        """
        Seralize a course object
        """
        students = [
            uc.user.serialize_course_user() for uc in self.users_in_course if uc.type == "student"
        ]
        instructors = [
            uc.user.serialize_course_user() for uc in self.users_in_course if uc.type == "instructor"
        ]
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "assignments": [a.serialize_course_assignment() for a in self.assignments],
            "students": students,
            "instructors": instructors,
        }

    def serialize_user_course(self):
        """
        Seralize a user in a course object
        """
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "assignments": None,
            "students": None,
            "instructors": None,
        }

class Assignment(db.Model):
    """
    Assignment model
    """
    __tablename__ = "assignment"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    due_date = db.Column(db.Integer, nullable=False) 
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    
    course = db.relationship("Course")

    def serialize(self):
        """
        Seralize a course object
        """
        return {
            "id": self.id,
            "title": self.title,
            "due_date": self.due_date,
            "course": self.course.serialize_user_course()
        }

    def serialize_course_assignment(self):
        """
        Seralize a assignment in a course object
        """
        return {
            "id": self.id,
            "title": self.title,
            "due_date": self.due_date,
            "course": None 
        }