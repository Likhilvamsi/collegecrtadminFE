from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Float, 
    ForeignKey, UniqueConstraint, Index, JSON, Date, Time,
    CheckConstraint
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# =========================================================
# 1. ROLES (Simple Role Management)
# =========================================================
class Role(Base):
    """
    User roles - Simple role management
    
    WHY NEEDED:
    - Different user types: ADMIN, TEACHER, STUDENT, COLLEGE_ADMIN
    - Each role has different permissions
    - Controls what user can see/do in the system
    
    ROLES:
    - ADMIN: System administrator (full access)
    - COLLEGE_ADMIN: College administrator (college-level management)
    - TEACHER: Instructor (create courses, tests, grade)
    - STUDENT: Learner (take courses, attempt tests)
    """
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint('name', name='uq_role_name'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)  # ADMIN, TEACHER, STUDENT, COLLEGE_ADMIN
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    users = relationship("User", back_populates="role")
    permissions = relationship(
        "Permission",
        back_populates="role",
        cascade="all, delete-orphan"
    )


class Permission(Base):
    """
    Role Permissions - What can each role do?
    
    WHY NEEDED:
    - Define what each role can access
    - Granular control (view, create, edit, delete per resource)
    - Easy to add new permissions without code change
    
    EXAMPLES:
    - TEACHER can view courses, create tests
    - STUDENT can view courses, take tests
    - ADMIN can approve colleges, manage users
    
    Use in code:
        if user.role.name == "TEACHER":
            show_create_test_button()
    """
    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint('role_id', 'action', 'resource', name='uq_permission'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(50), nullable=False)  # view, create, edit, delete, approve
    resource = Column(String(50), nullable=False)  # courses, tests, students, colleges
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    role = relationship("Role", back_populates="permissions")

    def __repr__(self):
        return f"<Permission {self.role_id}:{self.action}:{self.resource}>"


# =========================================================
# 2. USERS & AUTHENTICATION
# =========================================================
class User(Base):
    """
    Core User table - All user types use this
    
    LOGIN FLOW:
    
    STUDENT:
    - Login: email + password  OR  roll_number + password
    - Unique ID: email or phone
    - Example: john@example.com + password123
    
    TEACHER:
    - Login: email + password  OR  employee_id + password
    - Unique ID: email or employee_id
    - Example: teacher@college.com + password123
    
    ADMIN:
    - Login: email + password
    - Unique ID: email
    - Example: admin@system.com + password123
    
    COLLEGE_ADMIN:
    - Login: email + password
    - Unique ID: email
    - Example: collegeadmin@college.com + password123
    
    AuthToken is NOT stored permanently (only in memory/Redis)
    - Generate JWT when login successful
    - Store in Redis with 24-48 hour TTL
    - Database has no auth_tokens table
    - When logout, remove from Redis
    - No need to store in database
    """
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint('email', name='uq_user_email'),
        Index('idx_email', 'email'),
        Index('idx_role_id', 'role_id'),
        Index('idx_is_active', 'is_active'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)

    # Authentication
    full_name = Column(String(200), nullable=False)
    email = Column(String(150), nullable=False, unique=True)
    phone = Column(String(20), nullable=True)
    password_hash = Column(String(512), nullable=False)  # bcrypt

    # Profile
    bio = Column(Text, nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Activity
    last_login_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    role = relationship("Role", back_populates="users")
    student = relationship("Student", back_populates="user", uselist=False, cascade="all, delete-orphan")
    college_admin = relationship("CollegeAdmin", back_populates="user", uselist=False, cascade="all, delete-orphan")
    teacher = relationship("Teacher", back_populates="user", uselist=False, cascade="all, delete-orphan")

    notifications = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.email}>"


class PasswordReset(Base):
    """
    Password reset tokens - temporary tokens for password recovery
    
    FLOW:
    1. User clicks "Forgot Password"
    2. System generates reset_token
    3. Email sent to user with link: /reset?token=xyz123
    4. User enters new password
    5. Reset token marked used, expires after 24 hours
    """
    __tablename__ = "password_resets"
    __table_args__ = (
        Index('idx_user_reset', 'user_id'),
        Index('idx_token', 'reset_token'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reset_token = Column(String(500), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User")

    def __repr__(self):
        return f"<PasswordReset user_id={self.user_id}>"


class LoginHistory(Base):
    """
    Track login attempts - for security monitoring
    
    USE CASES:
    - Detect suspicious login patterns
    - Find successful login timeline
    - Identify failed login attempts
    - Security audit trail
    """
    __tablename__ = "login_history"
    __table_args__ = (
        Index('idx_user_login_at', 'user_id', 'login_at'),
        Index('idx_login_status', 'login_status'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    login_status = Column(String(20), nullable=False)  # SUCCESS, FAILED, BLOCKED
    ip_address = Column(String(45), nullable=True)
    reason_if_failed = Column(String(200), nullable=True)
    login_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship("User")

    def __repr__(self):
        return f"<LoginHistory user_id={self.user_id} status={self.login_status}>"


# =========================================================
# 3. COLLEGES & ORGANIZATIONAL STRUCTURE
# =========================================================
class College(Base):
    """
    College/Institution master data
    """
    __tablename__ = "colleges"
    __table_args__ = (
        UniqueConstraint('code', name='uq_college_code'),
        Index('idx_code', 'code'),
        Index('idx_is_active', 'is_active'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Basic Info
    name = Column(String(200), nullable=False, index=True)
    code = Column(String(50), nullable=True, unique=True)
    description = Column(Text, nullable=True)

    # Contact
    email = Column(String(150), nullable=True)
    phone = Column(String(20), nullable=True)
    website = Column(String(200), nullable=True)

    # Address
    city = Column(String(100), nullable=True, index=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), default="India", nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    established_year = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # ✅ Relationships
    college_courses = relationship(
        "CollegeCourse",
        back_populates="college",
        cascade="all, delete-orphan"
    )

    branches = relationship("CollegeBranch", back_populates="college", cascade="all, delete-orphan")
    academic_years = relationship("AcademicYear", back_populates="college", cascade="all, delete-orphan")
    students = relationship("Student", back_populates="college")
    admins = relationship("CollegeAdmin", back_populates="college")

    def __repr__(self):
        return f"<College {self.name}>"


class CollegeBranch(Base):
    """
    College departments/branches - CSE, ECE, ME, etc.
    """
    __tablename__ = "college_branches"
    __table_args__ = (
        UniqueConstraint('college_id', 'branch_code', name='uq_college_branch'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    college_id = Column(Integer, ForeignKey("colleges.id", ondelete="CASCADE"), nullable=False)

    branch_name = Column(String(100), nullable=False)  # CSE, ECE, Mechanical
    branch_code = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    college = relationship("College", back_populates="branches")
    students = relationship("Student", back_populates="branch")

    def __repr__(self):
        return f"<CollegeBranch {self.branch_name}>"


class AcademicYear(Base):
    """
    Academic year/batch - 2023-24, 2024-25, etc.
    """
    __tablename__ = "academic_years"
    __table_args__ = (
        UniqueConstraint('college_id', 'year_name', name='uq_college_year'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    college_id = Column(Integer, ForeignKey("colleges.id", ondelete="CASCADE"), nullable=False)

    year_name = Column(String(20), nullable=False)  # "2023-24"
    year_number = Column(Integer, nullable=True)  # 1, 2, 3 (for 1st, 2nd, 3rd year)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    college = relationship("College", back_populates="academic_years")
    students = relationship("Student", back_populates="academic_year")

    def __repr__(self):
        return f"<AcademicYear {self.year_name}>"


class CollegeAdmin(Base):
    """
    College administrator assignment
    """
    __tablename__ = "college_admins"
    __table_args__ = (
        UniqueConstraint('college_id', 'user_id', name='uq_college_admin'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    college_id = Column(Integer, ForeignKey("colleges.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    is_primary = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    college = relationship("College", back_populates="admins")
    user = relationship("User", back_populates="college_admin")

    def __repr__(self):
        return f"<CollegeAdmin college_id={self.college_id}>"


# =========================================================
# 4. STUDENTS
# =========================================================
class Student(Base):
    """
    Student profile and enrollment
    
    LOGIN:
    - Email + Password
    - OR Roll Number + Password
    - OR Student Unique ID + Password
    """
    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint('user_id', name='uq_student_user'),
        UniqueConstraint('student_unique_id', name='uq_student_unique_id'),
        Index('idx_college_id', 'college_id'),
        Index('idx_branch_id', 'branch_id'),
        Index('idx_enrollment_status', 'enrollment_status'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Educational Info
    college_id = Column(Integer, ForeignKey("colleges.id", ondelete="RESTRICT"), nullable=False)
    branch_id = Column(Integer, ForeignKey("college_branches.id", ondelete="RESTRICT"), nullable=False)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id", ondelete="RESTRICT"), nullable=False)

    # Identification
    roll_number = Column(String(50), nullable=True)
    student_unique_id = Column(String(100), nullable=False, unique=True)

    # Status
    enrollment_status = Column(String(20), default="ACTIVE", nullable=False)  # ACTIVE, INACTIVE, GRADUATED

    # Performance
    total_crt_score = Column(Float, default=0.0, nullable=False)
    total_tests_completed = Column(Integer, default=0, nullable=False)

    # Timestamps
    enrollment_date = Column(Date, default=datetime.now, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="student")
    college = relationship("College", back_populates="students")
    branch = relationship("CollegeBranch", back_populates="students")
    academic_year = relationship("AcademicYear", back_populates="students")

    course_enrollments = relationship("StudentCourse", back_populates="student", cascade="all, delete-orphan")
    test_attempts = relationship("TestAttempt", back_populates="student", cascade="all, delete-orphan")
    scores = relationship("StudentScore", back_populates="student", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Student {self.student_unique_id}>"


# =========================================================
# 5. TEACHER/INSTRUCTOR
# =========================================================
class Teacher(Base):
    """
    Teacher/Instructor profile
    
    LOGIN:
    - Email + Password
    - OR Employee ID + Password
    """
    __tablename__ = "teachers"
    __table_args__ = (
        UniqueConstraint('user_id', name='uq_teacher_user'),
        UniqueConstraint('employee_id', name='uq_teacher_employee_id'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    college_id = Column(Integer, ForeignKey("colleges.id", ondelete="RESTRICT"), nullable=False)

    # Identification
    employee_id = Column(String(50), nullable=False, unique=True)
    department = Column(String(100), nullable=True)

    # Experience
    years_of_experience = Column(Integer, default=0, nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="teacher")
    courses = relationship("Course", back_populates="teacher")

    def __repr__(self):
        return f"<Teacher {self.employee_id}>"


# =========================================================
# 6. COURSES & CONTENT
# =========================================================
class Course(Base):
    """
    CRT course / training material
    """
    __tablename__ = "courses"
    __table_args__ = (
        UniqueConstraint('course_code', name='uq_course_code'),
        Index('idx_code', 'course_code'),
        Index('idx_is_active', 'is_active'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)

    teacher_id = Column(
        Integer,
        ForeignKey("teachers.id", ondelete="SET NULL"),
        nullable=True
    )

    # Basic Information
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    course_code = Column(String(50), nullable=True, unique=True)

    # Classification
    category = Column(String(100), nullable=True)
    level = Column(String(20), default="BEGINNER", nullable=False)

    # Duration
    duration_hours = Column(Integer, nullable=True)
    expected_completion_days = Column(Integer, nullable=True)

    # Thumbnail
    thumbnail_url = Column(String(500), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_published = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # ✅ Relationships
    college_courses = relationship(
        "CollegeCourse",
        back_populates="course",
        cascade="all, delete-orphan"
    )

    teacher = relationship("Teacher", back_populates="courses")
    files = relationship("CourseFile", back_populates="course", cascade="all, delete-orphan")
    tests = relationship("Test", back_populates="course", cascade="all, delete-orphan")
    student_enrollments = relationship("StudentCourse", back_populates="course")

    def __repr__(self):
        return f"<Course {self.title}>"

class CollegeCourse(Base):
    """
    Mapping table between colleges and courses
    - One course can be used by many colleges
    - One college can take many courses
    """

    __tablename__ = "college_courses"
    __table_args__ = (
        UniqueConstraint("college_id", "course_id", name="uq_college_course"),
        Index("idx_college_id", "college_id"),
        Index("idx_course_id", "course_id"),
        Index("idx_is_active", "is_active"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)

    college_id = Column(
        Integer,
        ForeignKey("colleges.id", ondelete="CASCADE"),
        nullable=False
    )

    course_id = Column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False
    )

    # College-specific settings
    is_active = Column(Boolean, default=True, nullable=False)
    is_published = Column(Boolean, default=False, nullable=False)

    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    college = relationship("College", back_populates="college_courses")
    course = relationship("Course", back_populates="college_courses")

    def __repr__(self):
        return f"<CollegeCourse college_id={self.college_id} course_id={self.course_id}>"



class CourseFile(Base):
  
    __tablename__ = "course_files"
    __table_args__ = (
        Index('idx_course_id', 'course_id'),
        Index('idx_file_type', 'file_type'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)

    # File Information
    file_name = Column(String(255), nullable=False)
    file_title = Column(String(200), nullable=True)
    file_description = Column(Text, nullable=True)

    # File Metadata
    file_type = Column(String(20), nullable=False)  # PDF, VIDEO, DOCUMENT, IMAGE
    file_size = Column(Integer, nullable=True)  # in bytes
    mime_type = Column(String(100), nullable=True)

    # Storage URL (CDN)
    file_url = Column(String(500), nullable=False)  # Direct CDN download link

    # Additional Info
    duration_seconds = Column(Integer, nullable=True)  # For videos

    # Access Control
    is_published = Column(Boolean, default=True, nullable=False)
    download_allowed = Column(Boolean, default=True, nullable=False)

    # Analytics (tracked via code)
    download_count = Column(Integer, default=0, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)

    display_order = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    course = relationship("Course", back_populates="files")

    def __repr__(self):
        return f"<CourseFile {self.file_name}>"


# =========================================================
# 7. COURSE ENROLLMENTS
# =========================================================
class StudentCourse(Base):
    """
    Student course enrollment tracking
    """
    __tablename__ = "student_courses"
    __table_args__ = (
        UniqueConstraint('student_id', 'course_id', name='uq_student_course'),
        Index('idx_student_id', 'student_id'),
        Index('idx_course_id', 'course_id'),
        Index('idx_enrollment_status', 'enrollment_status'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)

    # Status
    enrollment_status = Column(String(20), default="ASSIGNED", nullable=False)  # ASSIGNED, IN_PROGRESS, COMPLETED, DROPPED

    # Progress
    progress_percentage = Column(Float, default=0.0, nullable=False)

    # Time Tracking
    start_date = Column(DateTime, nullable=True)
    completion_date = Column(DateTime, nullable=True)
    last_accessed_at = Column(DateTime, nullable=True)

    # Performance
    course_score = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    student = relationship("Student", back_populates="course_enrollments")
    course = relationship("Course", back_populates="student_enrollments")

    def __repr__(self):
        return f"<StudentCourse student_id={self.student_id} course_id={self.course_id}>"


# =========================================================
# 8. TESTS & ASSESSMENTS
# =========================================================
class Test(Base):
    """
    Test/Quiz/Assessment definitions
    """
    __tablename__ = "tests"
    __table_args__ = (
        UniqueConstraint('test_code', name='uq_test_code'),
        Index('idx_course_id', 'course_id'),
        Index('idx_is_published', 'is_published'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)

    # Basic Information
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    test_code = Column(String(50), nullable=True, unique=True)

    # Configuration
    total_marks = Column(Integer, nullable=False, default=100)
    passing_marks = Column(Integer, nullable=False, default=40)
    duration_minutes = Column(Integer, nullable=False, default=60)
    total_questions = Column(Integer, nullable=False, default=1)

    # Test Type
    test_type = Column(String(20), default="PRACTICE", nullable=False)  # QUIZ, MID_TERM, FINAL, PRACTICE
    difficulty_level = Column(String(20), default="MEDIUM", nullable=False)  # EASY, MEDIUM, HARD

    # Scheduling
    scheduled_date = Column(Date, nullable=True)
    scheduled_time = Column(Time, nullable=True)
    available_from = Column(DateTime, nullable=True)
    available_until = Column(DateTime, nullable=True)

    # Status
    is_published = Column(Boolean, default=False, nullable=False, index=True)

    # Settings
    instructions = Column(Text, nullable=True)
    show_answers_after_submission = Column(Boolean, default=False, nullable=False)
    allow_retake = Column(Boolean, default=True, nullable=False)
    max_retakes = Column(Integer, default=3, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    course = relationship("Course", back_populates="tests")
    attempts = relationship("TestAttempt", back_populates="test", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Test {self.title}>"


class TestAttempt(Base):
    """
    Student test submission/attempt
    """
    __tablename__ = "test_attempts"
    __table_args__ = (
        Index('idx_student_id', 'student_id'),
        Index('idx_test_id', 'test_id'),
        Index('idx_student_test', 'student_id', 'test_id'),
        Index('idx_attempt_status', 'attempt_status'),
        CheckConstraint('attempt_number >= 1', name='ck_attempt_positive'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    test_id = Column(Integer, ForeignKey("tests.id", ondelete="CASCADE"), nullable=False)

    # Attempt Details
    attempt_number = Column(Integer, default=1, nullable=False)

    # Performance
    marks_obtained = Column(Float, nullable=True)
    percentage = Column(Float, nullable=True)
    is_passed = Column(Boolean, nullable=True)

    # Timing
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    time_taken_seconds = Column(Integer, nullable=True)

    # Status
    attempt_status = Column(String(20), default="STARTED", nullable=False)  # STARTED, IN_PROGRESS, SUBMITTED, EVALUATED

    # Feedback
    feedback = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    student = relationship("Student", back_populates="test_attempts")
    test = relationship("Test", back_populates="attempts")

    def __repr__(self):
        return f"<TestAttempt student_id={self.student_id} attempt={self.attempt_number}>"


# =========================================================
# 9. STUDENT SCORES
# =========================================================
class StudentScore(Base):
    """
    Aggregate student performance scores
    """
    __tablename__ = "student_scores"
    __table_args__ = (
        Index('idx_student_id', 'student_id'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Overall Performance
    total_crt_score = Column(Float, default=0.0, nullable=False)

    # Test Performance
    total_tests_attempted = Column(Integer, default=0, nullable=False)
    total_tests_passed = Column(Integer, default=0, nullable=False)
    average_test_score = Column(Float, default=0.0, nullable=False)

    # Course Performance
    total_courses_assigned = Column(Integer, default=0, nullable=False)
    total_courses_completed = Column(Integer, default=0, nullable=False)

    # Overall Percentage
    overall_percentage = Column(Float, default=0.0, nullable=False)

    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    student = relationship("Student", back_populates="scores")

    def __repr__(self):
        return f"<StudentScore student_id={self.student_id} score={self.total_crt_score}>"


# =========================================================
# 10. RANKINGS
# =========================================================
class Ranking(Base):
    """
    Student rankings - college and branch-wise
    """
    __tablename__ = "rankings"
    __table_args__ = (
        UniqueConstraint('student_id', 'ranking_type', 'academic_year_id', name='uq_ranking'),
        Index('idx_student_id', 'student_id'),
        Index('idx_college_id', 'college_id'),
        Index('idx_rank_position', 'rank_position'),
        CheckConstraint('rank_position >= 1', name='ck_rank_positive'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)

    # Context
    college_id = Column(Integer, ForeignKey("colleges.id", ondelete="CASCADE"), nullable=False)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=True)

    # Ranking Details
    ranking_type = Column(String(20), nullable=False)  # COLLEGE_OVERALL, BRANCH_OVERALL
    rank_position = Column(Integer, nullable=False, index=True)
    total_students_ranked = Column(Integer, nullable=False)
    percentile_rank = Column(Float, nullable=True)

    # Performance Snapshot
    score_at_ranking = Column(Float, nullable=False)

    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    student = relationship("Student")

    def __repr__(self):
        return f"<Ranking student_id={self.student_id} rank={self.rank_position}>"


# =========================================================
# 11. NOTIFICATIONS
# =========================================================
class Notification(Base):
    """
    System notifications for users
    """
    __tablename__ = "notifications"
    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_is_read', 'is_read'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Notification Details
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False)  # COURSE_ASSIGNED, TEST_PUBLISHED, SCORE_UPDATED, etc.

    # Status
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)

    # Action
    action_url = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification user_id={self.user_id}>"


# =========================================================
# 12. AUDIT LOG (Simple)
# =========================================================
class AuditLog(Base):
    """
    Audit trail for critical operations
    
    REMOVED:
    - created_by (not needed for colleges)
    - approved_by (not needed for colleges)
    - approval_notes (not needed for colleges)
    
    KEPT:
    - Track who did what, when
    - For compliance and debugging
    """
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_action_type', 'action_type'),
        Index('idx_created_at', 'created_at'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Action
    action_type = Column(String(100), nullable=False)  # create_course, update_test, etc.
    description = Column(String(500), nullable=True)

    # Entity Changed
    entity_type = Column(String(50), nullable=True)  # Student, Course, Test
    entity_id = Column(Integer, nullable=True)

    # Changes
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)

    # Status
    status = Column(String(20), default="SUCCESS", nullable=False)  # SUCCESS, FAILURE

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship("User")

    def __repr__(self):
        return f"<AuditLog action={self.action_type}>"


# =========================================================
# DATABASE HELPERS
# =========================================================

def init_database(engine):
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)
    print("✓ Database initialized")


def drop_all_tables(engine):
    """Drop all tables (use with caution)"""
    Base.metadata.drop_all(bind=engine)
    print("✓ All tables dropped")


