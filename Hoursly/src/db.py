from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# --- UserSavedOfficeHour Model ---
class UserSavedOfficeHour(db.Model):
    """
    UserSavedOfficeHour model: Many-to-Many relationship between User and OfficeHour
    Allows a student to 'save' an office hour slot.
    """
    __tablename__ = "user_saved_oh"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    oh_id = db.Column(db.Integer, db.ForeignKey("office_hour.id"), nullable=False)
    
    user = db.relationship("User", back_populates="saved_office_hours")
    office_hour = db.relationship("OfficeHour", back_populates="saved_by_users")

    def serialize_oh_in_user(self):
        """
        Serialize the full office hour object 
        """
        return self.office_hour.serialize()


# --- OfficeHour Model ---
class OfficeHour(db.Model):
    """
    OfficeHour model
    """
    __tablename__ = "office_hour"
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String, nullable=False) 
    start_time = db.Column(db.String, nullable=False)
    end_time = db.Column(db.String, nullable=False) 
    location = db.Column(db.String, nullable=False) 
    

    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    ta_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    
    # Relationships
    course = db.relationship("Course", back_populates="office_hours")
    ta = db.relationship("User", back_populates="office_hours_ta")
    saved_by_users = db.relationship("UserSavedOfficeHour", back_populates="office_hour", cascade="all, delete")

    def serialize(self):
        """
        Seralize a full office hour object
        """
        return {
            "id": self.id,
            "day": self.day,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "location": self.location,
            "course": self.course.serialize_user_course(),
            "ta": self.ta.serialize_office_hour_ta()
        }

    def serialize_course_oh(self):
        """
        Seralize an office hour within a course object
        """
        return {
            "id": self.id,
            "day": self.day,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "location": self.location,
            "ta": self.ta.serialize_office_hour_ta()
        }

# --- StudentToCourse Model ---
class StudentToCourse(db.Model):
    """
    StudentToCourse model: Links User (as student) to Course
    """
    __tablename__ = "student_to_course"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    
    user = db.relationship("User", back_populates="student_courses")
    course = db.relationship("Course", back_populates="students_in_course")

    def serialize_course_in_user(self):
        """
        Seralize a student's course object
        """
        return self.course.serialize_user_course()

# --- InstructorToCourse Model ---
class InstructorToCourse(db.Model):
    """
    InstructorToCourse model: Links User (as instructor or TA) to Course
    """
    __tablename__ = "instructor_to_course"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    type = db.Column(db.String, nullable=False)
    
    user = db.relationship("User", back_populates="instructor_courses")
    course = db.relationship("Course", back_populates="instructors_in_course")

    def serialize_course_in_user(self):
        """
        Seralize an instructor/TA's course object
        """
        return self.course.serialize_user_course()


# --- User Model ---
class User(db.Model):
    """
    User model
    """
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    netid = db.Column(db.String, nullable=False)
    
    # FIX: Replaced incorrect UserToCourse relationship with StudentToCourse and InstructorToCourse
    student_courses = db.relationship("StudentToCourse", back_populates="user", cascade="all, delete")
    instructor_courses = db.relationship("InstructorToCourse", back_populates="user", cascade="all, delete")

    office_hours_ta = db.relationship("OfficeHour", back_populates="ta", cascade="all, delete")
    saved_office_hours = db.relationship("UserSavedOfficeHour", back_populates="user", cascade="all, delete") 

    def serialize(self):
        """
        Seralize a user object
        """
        # FIX: Combine courses from both student and instructor/TA relationships
        all_courses = [c.serialize_course_in_user() for c in self.student_courses] + \
                      [c.serialize_course_in_user() for c in self.instructor_courses]

        return {
            "id": self.id,
            "name": self.name,
            "netid": self.netid,
            "courses": all_courses,
            "saved_office_hours": [soh.serialize_oh_in_user() for soh in self.saved_office_hours] 
        }

    def serialize_course_user(self):
        """
        Seralize a user in a course object
        """
        return {
            "id": self.id,
            "name": self.name,
            "netid": self.netid,
            "courses": None
        }
        
    def serialize_office_hour_ta(self):
        """
        Seralize a TA in an office hour object
        """
        return {
            "id": self.id,
            "name": self.name,
            "netid": self.netid,
        }

# --- Course Model ---
class Course(db.Model):
    """
    Course model
    """
    __tablename__ = "course"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    
    # FIX: Replaced incorrect UserToCourse relationship with StudentToCourse and InstructorToCourse
    students_in_course = db.relationship("StudentToCourse", back_populates="course", cascade="all, delete")
    instructors_in_course = db.relationship("InstructorToCourse", back_populates="course", cascade="all, delete")
    
    office_hours = db.relationship("OfficeHour", back_populates="course", cascade="all, delete")

    def serialize(self):
        """
        Seralize a course object
        """
        # FIX: Fetch students from the dedicated students_in_course relationship
        students = [
            uc.user.serialize_course_user() for uc in self.students_in_course
        ]
        
        # FIX: Fetch instructors and TAs from the dedicated instructors_in_course relationship
        instructors = []
        tas = []
        for uc in self.instructors_in_course:
            if uc.type == "instructor":
                instructors.append(uc.user.serialize_course_user())
            elif uc.type == "TA":
                tas.append(uc.user.serialize_course_user())

        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "students": students,
            "instructors": instructors,
            "tas": tas,
            "office_hours": [oh.serialize_course_oh() for oh in self.office_hours]
        }

    def serialize_user_course(self):
        """
        Seralize a course object 
        """
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "students": None,
            "instructors": None,
            "tas": None,
            "office_hours": None,
        }