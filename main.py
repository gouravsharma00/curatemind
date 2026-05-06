from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import jwt
import random
import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader

# --- App Config ---
SECRET_KEY = "super-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Load environment variables from .env
load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("defpneqxf"),
    api_key=os.getenv("967119597615287"),
    api_secret=os.getenv("Zx-IbAWoSyzomb6-cFUg_sRZCoA"),
    secure=True
)

# --- Path Config ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Database Setup ---
# We are using SQLite for local development. It stores the entire database in a single file ('curatemind.db').
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./curatemind_v2.db")

# The 'engine' is the core interface to the database. 
# 'check_same_thread': False is required for SQLite in FastAPI so multiple requests can share the same connection.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 'SessionLocal' is a factory that generates new database sessions for each request.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 'Base' is the declarative base class. All of our database models will inherit from this.
Base = declarative_base()

# --- Database Models (Tables) ---
class User(Base):
    # Represents the 'users' table in the database
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    
    # New columns for personalization (Phase 2)
    full_name = Column(String(255), nullable=True) # User's full name
    # nullable=True means these can be empty until the user completes the assessment/onboarding
    interests = Column(String(255), nullable=True) # Stores comma-separated tags like "python,ml,react"
    tier = Column(String(50), nullable=True)       # Stores their skill level: Beginner, Intermediate, or Advanced
    role = Column(String(50), default="student")   # Role-Based Access Control: 'student' or 'admin'
    profile_picture_url = Column(String(500), nullable=True) # Cloudinary URL

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String(50), index=True)
    question_text = Column(String(500))
    option_a = Column(String(255))
    option_b = Column(String(255))
    option_c = Column(String(255))
    option_d = Column(String(255))
    correct_answer = Column(String(255))

class Course(Base):
    # Represents the 'courses' table in the database
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    description = Column(String(500))
    tags = Column(String(255)) # Used for our recommendation engine (e.g., "python,data-science")
    level = Column(String(50)) # Beginner, Intermediate, or Advanced

# Auto-creates the tables in the SQLite database if they don't already exist.
Base.metadata.create_all(bind=engine)

# --- Schemas ---
# Pydantic Models (Schemas) validate the incoming JSON payloads from the frontend.
# Think of them as strict gatekeepers. Once the frontend JSON passes validation here, 
# we extract the properties and map them to our SQLAlchemy Database Models to actually save to SQLite.
class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    admin_code: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class OnboardingUpdate(BaseModel):
    user_id: int
    interests: str

class AssessmentUpdate(BaseModel):
    user_id: int
    tier: str

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    interests: str
    tier: str

class QuizSubmission(BaseModel):
    user_id: int
    topic: str
    answers: dict[int, int]

class AssessmentScoreUpdate(BaseModel):
    score: int
    total_questions: int

class CourseCreate(BaseModel):
    user_id: int
    title: str
    description: str

class MentorConnectRequest(BaseModel):
    mentor_name: str

class QuestionCreate(BaseModel):
    topic: str
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str

# --- Security ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- FastAPI App ---
# --- 1. IMPORTS MUST GO FIRST ---
from fastapi import FastAPI
from fastapi.responses import FileResponse
# (Keep any other imports you already have right here, like passlib or sqlite3)

# --- 2. DEFINE THE APP SECOND ---
app = FastAPI()

# --- 3. ADD THE ROOT ROUTE THIRD ---
@app.get("/")
async def get_root_index():
    return FileResponse("index.html")

# --- 4. ALL OTHER ROUTES GO BELOW ---
# Keep all your existing routes (like dashboard, login, etc.) down here!
app = FastAPI()
@app.get("/auth.html")
async def get_auth_page():
    return FileResponse("auth.html")

@app.get("/onboarding.html")
async def get_onboarding_page():
    return FileResponse("onboarding.html")

# Run the seed_courses function when the server starts up
@app.get("/assessment.html")
async def get_assessment_page():
    return FileResponse("assessment.html")

@app.get("/dashboard.html")
async def get_dashboard_page():
    return FileResponse("dashboard.html")

@app.get("/profile.html")
async def get_profile_page():
    return FileResponse("profile.html")

@app.get("/catalog.html")
async def get_catalog_page():
    return FileResponse("catalog.html")
@app.get("/admin_dashboard.html")
async def get_admin_dashboard_page():
    return FileResponse("admin_dashboard.html")

@app.get("/index.html")
async def get_index_page():
    return FileResponse("index.html")
@app.on_event("startup")
def startup_event():
    seed_courses()
    seed_questions()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Assessment Questions Bank ---
ASSESSMENT_QUESTIONS = {
    "python": [
        {"id": 1, "question": "What is a 'DataFrame' in Pandas?", "options": ["A 2-dimensional labeled data structure", "A type of neural network layer", "An SQL database engine", "A metric for measuring model error"], "answer": 0, "weight": 1},
        {"id": 2, "question": "Which keyword is used to define a function in Python?", "options": ["func", "def", "function", "lambda"], "answer": 1, "weight": 1},
        {"id": 3, "question": "What does __init__ do in a Python class?", "options": ["Deletes an object", "Imports a module", "Initializes a new object", "Compiles the code"], "answer": 2, "weight": 1},
    ],
    "react": [
        {"id": 4, "question": "What is JSX?", "options": ["A CSS framework", "A syntax extension for JavaScript", "A database query language", "A state management tool"], "answer": 1, "weight": 1},
        {"id": 5, "question": "Which hook is used to manage state in a functional component?", "options": ["useEffect", "useContext", "useState", "useReducer"], "answer": 2, "weight": 1},
        {"id": 6, "question": "What are React components?", "options": ["HTML templates", "Reusable pieces of UI", "Database tables", "Server-side routes"], "answer": 1, "weight": 1},
    ],
    # Future topics initialized with empty arrays to prevent key errors
    "sql": [],
    "deep-learning": [],
    "ml": [],
    "javascript": [],
    "data-science": [],
    "statistics": [],
    "backend": [],
    "frontend": [],
    "devops": [],
    "mlops": [],
    "systems": []
}


# --- Database Seeding ---
def seed_courses():
    # Create a temporary database session just for seeding
    db = SessionLocal()
    try:
        # Check if the Course table is completely empty
        if db.query(Course).count() == 0:
            dummy_courses = [
                Course(title="Python for Beginners", description="Start your coding journey with Python.", tags="python", level="Beginner"),
                Course(title="React Crash Course", description="Build modern web apps with React.", tags="react,frontend", level="Beginner"),
                Course(title="Data Science with Pandas", description="Analyze data efficiently.", tags="python,data-science", level="Intermediate"),
                Course(title="Intro to Machine Learning", description="Learn the basics of ML algorithms.", tags="python,ml", level="Intermediate"),
                Course(title="Advanced Deep Learning", description="Neural networks and beyond.", tags="python,ml,deep-learning", level="Advanced"),
                Course(title="Fullstack React & FastAPI", description="Connect your frontend to a real backend.", tags="react,backend,python", level="Advanced"),
            ]
            # Add all dummy courses to the transaction and commit to the database
            db.add_all(dummy_courses)
            db.commit()
            print("Successfully seeded the database with 6 dummy courses.")
    finally:
        db.close()

def seed_questions():
    db = SessionLocal()
    try:
        if db.query(Question).count() == 0:
            dummy_questions = [
                # Python
                Question(topic="python", question_text="What is a 'DataFrame' in Pandas?", option_a="A 2-dimensional labeled data structure", option_b="A type of neural network layer", option_c="An SQL database engine", option_d="A metric for measuring model error", correct_answer="A 2-dimensional labeled data structure"),
                Question(topic="python", question_text="Which keyword is used to define a function in Python?", option_a="func", option_b="def", option_c="function", option_d="lambda", correct_answer="def"),
                Question(topic="python", question_text="What does __init__ do in a Python class?", option_a="Deletes an object", option_b="Imports a module", option_c="Initializes a new object", option_d="Compiles the code", correct_answer="Initializes a new object"),
                # React
                Question(topic="react", question_text="What is JSX?", option_a="A CSS framework", option_b="A syntax extension for JavaScript", option_c="A database query language", option_d="A state management tool", correct_answer="A syntax extension for JavaScript"),
                Question(topic="react", question_text="Which hook is used to manage state in a functional component?", option_a="useEffect", option_b="useContext", option_c="useState", option_d="useReducer", correct_answer="useState"),
                Question(topic="react", question_text="What are React components?", option_a="HTML templates", option_b="Reusable pieces of UI", option_c="Database tables", option_d="Server-side routes", correct_answer="Reusable pieces of UI"),
                # SQL
                Question(topic="sql", question_text="Which clause is used to filter the results of a query?", option_a="ORDER BY", option_b="WHERE", option_c="GROUP BY", option_d="SELECT", correct_answer="WHERE"),
                Question(topic="sql", question_text="What does SQL stand for?", option_a="Structured Query Language", option_b="Strong Question Language", option_c="Structured Question Language", option_d="Simple Query Language", correct_answer="Structured Query Language"),
                Question(topic="sql", question_text="Which statement is used to extract data from a database?", option_a="EXTRACT", option_b="GET", option_c="OPEN", option_d="SELECT", correct_answer="SELECT"),
                # JavaScript
                Question(topic="javascript", question_text="Which symbol is used for comments in JavaScript?", option_a="//", option_b="/*", option_c="<!--", option_d="#", correct_answer="//"),
                Question(topic="javascript", question_text="What is a closure in JavaScript?", option_a="A function having access to the parent scope", option_b="A loop that never ends", option_c="A type of variable", option_d="An error handler", correct_answer="A function having access to the parent scope"),
                Question(topic="javascript", question_text="How do you declare a block-scoped variable?", option_a="var", option_b="let", option_c="const", option_d="Both b and c", correct_answer="Both b and c"),
                # Data Science
                Question(topic="data-science", question_text="Which metric is used for classification models?", option_a="Mean Squared Error", option_b="R-squared", option_c="F1-Score", option_d="Accuracy", correct_answer="Accuracy"),
                Question(topic="data-science", question_text="What does EDA stand for?", option_a="Exploratory Data Analysis", option_b="External Data Alignment", option_c="Exact Data Algorithm", option_d="End Data Assessment", correct_answer="Exploratory Data Analysis"),
                Question(topic="data-science", question_text="What is a heatmap often used for?", option_a="Viewing source code", option_b="Visualizing correlation matrices", option_c="Printing text", option_d="Connecting databases", correct_answer="Visualizing correlation matrices"),
                # Statistics
                Question(topic="statistics", question_text="What is the median of [1, 3, 3, 6, 7, 8, 9]?", option_a="3", option_b="6", option_c="5", option_d="7", correct_answer="6"),
                Question(topic="statistics", question_text="What does standard deviation measure?", option_a="The center of data", option_b="The spread of data", option_c="The total sum of data", option_d="The maximum value", correct_answer="The spread of data"),
                Question(topic="statistics", question_text="In a normal distribution, what percentage of data falls within one standard deviation?", option_a="50%", option_b="68%", option_c="95%", option_d="99.7%", correct_answer="68%"),
                # Backend
                Question(topic="backend", question_text="What does an API do?", option_a="Styles a web page", option_b="Communicates between systems", option_c="Renders HTML", option_d="Manages computer hardware", correct_answer="Communicates between systems"),
                Question(topic="backend", question_text="Which status code indicates 'Not Found'?", option_a="200", option_b="301", option_c="404", option_d="500", correct_answer="404"),
                Question(topic="backend", question_text="What does ORM stand for?", option_a="Object-Relational Mapping", option_b="Online Resource Manager", option_c="Operational Route Model", option_d="Objective Rendering Method", correct_answer="Object-Relational Mapping"),
                # Frontend
                Question(topic="frontend", question_text="What does CSS stand for?", option_a="Cascading Style Sheets", option_b="Computer Style Systems", option_c="Creative Style Syntax", option_d="Coded Site Styles", correct_answer="Cascading Style Sheets"),
                Question(topic="frontend", question_text="Which HTML tag is used for the largest heading?", option_a="<header>", option_b="<h6>", option_c="<heading>", option_d="<h1>", correct_answer="<h1>"),
                Question(topic="frontend", question_text="What does the 'alt' attribute in an image tag do?", option_a="Adds a tooltip", option_b="Defines alternative text", option_c="Resizes the image", option_d="Makes the image clickable", correct_answer="Defines alternative text"),
                # DevOps
                Question(topic="devops", question_text="What does CI/CD stand for?", option_a="Continuous Integration / Continuous Deployment", option_b="Code Integration / Code Delivery", option_c="Custom Implementation / Custom Design", option_d="Centralized Information / Centralized Data", correct_answer="Continuous Integration / Continuous Deployment"),
                Question(topic="devops", question_text="Which tool is used for containerization?", option_a="Docker", option_b="Photoshop", option_c="Excel", option_d="Word", correct_answer="Docker"),
                Question(topic="devops", question_text="What is a primary goal of DevOps?", option_a="Writing slower code", option_b="Bridging development and operations", option_c="Eliminating databases", option_d="Designing UI", correct_answer="Bridging development and operations"),
                # MLOps
                Question(topic="mlops", question_text="What is the main focus of MLOps?", option_a="Designing websites", option_b="Deploying and maintaining ML models", option_c="Creating databases", option_d="Writing CSS", correct_answer="Deploying and maintaining ML models"),
                Question(topic="mlops", question_text="Which problem does model drift refer to?", option_a="A model's predictive power degrading over time", option_b="A model moving to a new server", option_c="A model learning too fast", option_d="A model's training data expanding", correct_answer="A model's predictive power degrading over time"),
                Question(topic="mlops", question_text="Which tool is commonly used for ML experiment tracking?", option_a="MLflow", option_b="React", option_c="Nginx", option_d="Redis", correct_answer="MLflow"),
                # Systems
                Question(topic="systems", question_text="What is an operating system kernel?", option_a="A web browser", option_b="The core component that manages system resources", option_c="A text editor", option_d="A programming language", correct_answer="The core component that manages system resources"),
                Question(topic="systems", question_text="What is virtual memory?", option_a="A physical hard drive", option_b="A technique that gives the illusion of larger main memory", option_c="A cloud database", option_d="A network protocol", correct_answer="A technique that gives the illusion of larger main memory"),
                Question(topic="systems", question_text="What does CPU stand for?", option_a="Central Processing Unit", option_b="Computer Personal Unit", option_c="Central Printed Utility", option_d="Control Panel Utility", correct_answer="Central Processing Unit"),
            ]
            db.add_all(dummy_questions)
            db.commit()
            print("Successfully seeded the database with 33 dummy questions.")
    finally:
        db.close()

# Dependency function to provide a database session to our API endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- API Endpoints ---
@app.get("/")
def serve_frontend():
    FRONTEND_PATH = os.path.join(BASE_DIR, 'auth.html')
    if not os.path.exists(FRONTEND_PATH):
        return {
            "error": f"File not found at {FRONTEND_PATH}",
            "files_in_dir": os.listdir(BASE_DIR)
        }
    return FileResponse(FRONTEND_PATH)

@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    role = "admin" if user.admin_code == "admin02" else "student"
    hashed_pw = pwd_context.hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_pw, role=role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user) # Refreshes the instance to get the auto-generated ID
    return {"message": "User created", "user_id": new_user.id, "role": new_user.role}

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not pwd_context.verify(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    return {"message": "Login successful", "user_id": db_user.id, "role": db_user.role, "access_token": access_token, "token_type": "bearer"}

@app.post("/save_onboarding")
def save_onboarding(data: OnboardingUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.interests = data.interests
    db.commit()
    return {"message": "Onboarding saved successfully"}

@app.post("/save_assessment")
def save_assessment(data: AssessmentUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.tier = data.tier
    db.commit()
    return {"message": "Assessment saved successfully"}

@app.get("/assessment/{topic}")
def get_assessment_questions(topic: str, db: Session = Depends(get_db)):
    topic_lower = topic.lower()
    questions = db.query(Question).filter(Question.topic == topic_lower).all()
    
    if not questions:
        raise HTTPException(status_code=404, detail=f"Questions for '{topic}' are coming soon!")

    selected_questions = random.sample(questions, min(len(questions), 3))

    safe_questions = []
    for q in selected_questions:
        safe_q = {"id": q.id, "question": q.question_text, "options": [q.option_a, q.option_b, q.option_c, q.option_d], "correct_answer": q.correct_answer, "weight": 1}
        safe_questions.append(safe_q)
        
    return safe_questions

@app.post("/submit_assessment")
def submit_assessment(data: QuizSubmission, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    topic_lower = data.topic.lower()
    if topic_lower not in ASSESSMENT_QUESTIONS:
        raise HTTPException(status_code=400, detail="Invalid topic")
        
    score = 0
    for q in ASSESSMENT_QUESTIONS[topic_lower]:
        # Check if the user's answer matches the correct answer
        if q["id"] in data.answers and data.answers[q["id"]] == q["answer"]:
            score += 1
            
    # Tier calculation logic
    tier = "Beginner" if score <= 1 else "Intermediate" if score == 2 else "Advanced"
    user.tier = tier
    db.commit()
    return {"message": "Quiz graded", "score": score, "total": len(ASSESSMENT_QUESTIONS[topic_lower]), "tier": tier}

@app.post("/submit_assessment/{user_id}")
def submit_assessment_score(user_id: int, data: AssessmentScoreUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    percentage = (data.score / data.total_questions) * 100 if data.total_questions > 0 else 0
    
    if percentage <= 40:
        tier = "Beginner"
    elif percentage <= 79:
        tier = "Intermediate"
    else:
        tier = "Advanced"
        
    user.tier = tier
    db.commit()
    return {"message": "Tier assigned successfully", "tier": tier, "percentage": percentage}

@app.get("/user/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"full_name": user.full_name, "email": user.email, "tier": user.tier, "interests": user.interests}

@app.put("/update_profile/{user_id}")
def update_profile(user_id: int, data: ProfileUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if data.full_name is not None:
        user.full_name = data.full_name
    user.interests = data.interests
    user.tier = data.tier
    db.commit()
    return {"message": "Profile updated successfully"}

@app.post("/upload_profile_picture/{user_id}")
async def upload_profile_picture(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Upload file directly to Cloudinary
        result = cloudinary.uploader.upload(file.file)
        secure_url = result.get("secure_url")
        
        # Save the secure URL to the database
        user.profile_picture_url = secure_url
        db.commit()
        
        return {"message": "Profile picture updated successfully", "secure_url": secure_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloudinary upload failed: {str(e)}")

@app.get("/recommendations/{user_id}")
def get_recommendations(user_id: int, db: Session = Depends(get_db)):
    # 1. Fetch User Data
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 2. Edge Case Handling
    # If the user hasn't completed onboarding/assessment, they won't have a tier or interests.
    if not user.tier or not user.interests:
        # Fallback: Return all 'Beginner' courses as a safe default
        fallback_courses = db.query(Course).filter(Course.level == "Beginner").all()
        return fallback_courses

    # 3. Hybrid Filtering Logic
    # Step A: Rule-Based Filter 
    # First, we narrow down the universe of courses to ONLY those that match the user's skill tier.
    level_matched_courses = db.query(Course).filter(Course.level == user.tier).all()

    # Step B: Content-Based Filter
    # Now, we take the tier-matched courses and filter them by the user's specific interests.
    # We convert the comma-separated strings into Sets so we can easily check for intersections.
    user_interests_set = set([i.strip().lower() for i in user.interests.split(",")])
    
    recommended_courses = []
    for course in level_matched_courses:
        if course.tags:
            course_tags_set = set([t.strip().lower() for t in course.tags.split(",")])
            # If there's an overlap between what the user likes and what the course covers, keep it!
            if user_interests_set.intersection(course_tags_set):
                recommended_courses.append(course)
                
    # Return the final curated array of courses. 
    # If content-filtering was too strict and returned empty, safely fallback to the level-matched list.
    return recommended_courses if recommended_courses else level_matched_courses

@app.get("/courses")
def get_courses(topic: str = None, search: str = None, db: Session = Depends(get_db)):
    query = db.query(Course)
    
    # 1. Handle the Category Buttons
    if topic and topic.lower() != 'all':
        # Map frontend topics to our seeded database tags
        topic_mapping = {
            "machine learning": "ml",
            "data science": "data-science",
            "web dev": "react"
        }
        db_tag = topic_mapping.get(topic.lower(), topic.lower())
        query = query.filter(Course.tags.ilike(f"%{db_tag}%"))
        
    # 2. Handle the Search Bar
    if search:
        query = query.filter(Course.title.ilike(f"%{search}%") | Course.description.ilike(f"%{search}%"))
        
    # FastAPI will automatically serialize this list of database objects into JSON
    return query.all()

@app.post("/create_course")
def create_course(data: CourseCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == data.user_id).first()
    
    # Check RBAC logic to ensure only Admins hit this route
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
        
    # Dummy logic to represent creating a course
    # In a fully fleshed app, you would save actual course rows to your Course model here.
    return {"message": f"Course '{data.title}' created successfully by Admin!"}

@app.get("/admin/question_counts")
def get_question_counts(db: Session = Depends(get_db)):
    # Group questions by topic and count them using SQLAlchemy's func.count
    counts = db.query(Question.topic, func.count(Question.id)).group_by(Question.topic).all()
    
    # Initialize dictionary with defaults
    results = {"python": 0, "react": 0, "sql": 0, "ml": 0, "deep-learning": 0}
    for topic, count in counts:
        topic_lower = topic.lower()
        if topic_lower in results:
            results[topic_lower] = count
        else:
            results[topic_lower] = count
            
    return results

@app.post("/admin/add_question")
def add_question(data: QuestionCreate, db: Session = Depends(get_db)):
    new_q = Question(
        topic=data.topic.lower(),
        question_text=data.question_text,
        option_a=data.option_a, option_b=data.option_b, option_c=data.option_c, option_d=data.option_d,
        correct_answer=data.correct_answer
    )
    db.add(new_q)
    db.commit()
    return {"message": "Question added successfully to the master bank!"}

@app.post("/api/connect_mentor")
def connect_mentor(data: MentorConnectRequest):
    print(f"Connection request logged for {data.mentor_name}")
    return {"status": "success", "message": "Connected"}

# --- Serve Static Frontend Files ---
# Mount the directory containing your HTML/CSS/JS files so they can be accessed directly.
# We put this at the very bottom so it acts as a catch-all and doesn't override our API routes.
app.mount("/static", StaticFiles(directory=BASE_DIR), name="static")