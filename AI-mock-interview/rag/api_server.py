from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Tuple
import io
import re
import PyPDF2
import docx
import os
import sqlite3
import json
import random
import traceback
from dotenv import load_dotenv

# Import helper functions from the existing application
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database_helpers import (load_conversation, save_conversation, 
                             clear_conversation, init_db, create_user, 
                             login_user, get_user_id)
from report_generation import generate_report
from query_pinecone import query_pinecone
from llm_setup import get_prompt_template, generate_user_info

# LLM imports
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain.schema.runnable import RunnableSequence

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Explicitly create user_preferences table
conn = sqlite3.connect("app.db")
c = conn.cursor()
print("Creating user_preferences table if it doesn't exist...")
c.execute('''
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id INTEGER PRIMARY KEY,
    interview_type TEXT DEFAULT 'technical'
)
''')
conn.commit()
conn.close()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get API keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set")

# Database setup
init_db()

# Pydantic models
class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    user_id: int
    username: str
    success: bool
    message: str

class InterviewSetup(BaseModel):
    job_description: str
    user_id: int
    interview_type: str = "technical"  # Add interview type field with default "technical"
    
    def __init__(self, **data):
        # Convert interview_type to lowercase if present
        if "interview_type" in data:
            data["interview_type"] = data["interview_type"].lower()
        super().__init__(**data)

class InterviewMessage(BaseModel):
    message: str
    user_id: int

class InterviewSessionState(BaseModel):
    current_topic: Optional[str] = None
    explored_topics: List[str] = []
    questions_in_current_topic: int = 0
    last_question_type: str = "introduction"
    concepts_covered: Dict[str, List[str]] = {}
    current_concept: Optional[str] = None
    current_difficulty: str = "easy"  # easy, medium, hard
    question_count_in_concept: int = 0

# Helper functions
def extract_text_from_file(file_content, filename):
    file_extension = filename.split(".")[-1].lower()
    if file_extension == "txt":
        try:
            return file_content.decode("utf-8", errors="ignore")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading TXT file: {str(e)}")
    elif file_extension == "pdf":
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
            return text
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error processing PDF file: {str(e)}")
    elif file_extension == "docx":
        try:
            doc = docx.Document(io.BytesIO(file_content))
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error processing DOCX file: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format!")

# Resume extraction function from new_app1.py
def extract_resume_details(text):
    details = {
        "NAME": "",
        "SKILLS": "",
        "WORK_EXPERIENCE": "",
        "PROJECTS": ""
    }
    
    # Simplified extraction logic (case-insensitive)
    # Name extraction (assume first non-empty line might be name or after "name:" or "resume:")
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if line and not details["NAME"]:
            # Check for common resume headers to skip
            if not any(header.lower() in line.lower() for header in ["resume", "cv", "curriculum"]):
                details["NAME"] = line
                break
    
    # Skills extraction
    skills_section = False
    skills_text = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if re.search(r'skills|technologies|technical', line, re.IGNORECASE):
            skills_section = True
            continue
        elif skills_section and re.search(r'education|experience|projects|certifications', line, re.IGNORECASE):
            skills_section = False
        
        if skills_section:
            skills_text.append(line)
    
    details["SKILLS"] = " ".join(skills_text)
    
    # Work experience extraction
    exp_section = False
    exp_text = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if re.search(r'work experience|professional experience|employment|career', line, re.IGNORECASE):
            exp_section = True
            continue
        elif exp_section and re.search(r'education|skills|projects|certifications', line, re.IGNORECASE):
            exp_section = False
        
        if exp_section:
            exp_text.append(line)
    
    details["WORK_EXPERIENCE"] = " ".join(exp_text)
    
    # Projects extraction
    proj_section = False
    proj_text = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if re.search(r'projects|personal projects', line, re.IGNORECASE):
            proj_section = True
            continue
        elif proj_section and re.search(r'education|skills|experience|certifications', line, re.IGNORECASE):
            proj_section = False
        
        if proj_section:
            proj_text.append(line)
    
    details["PROJECTS"] = " ".join(proj_text)
    
    return details

def initialize_llm(model):
    """Initialize the LLM with the selected model and API key."""
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY
    return ChatGroq(
        model=model,
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

def get_question_answer_context(user_info):
    """Fetches relevant interview questions from Pinecone."""
    query_results = query_pinecone(query=user_info, top_k=4)
    return [
        {"question": match["metadata"]["question"], "answer": match["metadata"]["answer"]}
        for match in query_results["matches"]
    ]

# Add a function to generate a personalized greeting using candidate's name
def generate_personalized_greeting(name):
    if not name or name.strip() == "":
        return "Hello! I'll be conducting your interview today. Could you start by telling me a bit about yourself and your background?"
    
    return f"Hello {name}! I'll be conducting your interview today. Could you start by telling me a bit about yourself and your background?"

# Add a function to get relevant questions from RAG
def get_rag_questions(job_description, resume_skills, interview_type):
    """
    Get relevant questions from RAG system based on job description,
    resume skills and interview type.
    """
    # Create a query from job description and skills for technical questions
    query = f"Interview questions for a candidate with skills in {resume_skills} applying for {job_description}"
    
    # Adjust query based on interview type
    if interview_type.lower() == "behavioral":
        query = f"Behavioral interview questions for a candidate applying for a position in {job_description}"
    
    # Get questions from Pinecone
    try:
        # Use the retrieve_relevant_qa function to get the most relevant questions
        from query_pinecone import retrieve_relevant_qa
        skill_keywords = [s.strip().lower() for s in resume_skills.split(',')]
        
        # Find the most relevant skill in our database
        relevant_skill = None
        for skill in skill_keywords:
            if skill in ["python", "sql", "data engineering", "machine learning", "etl", "aws"]:
                relevant_skill = skill
                break
        
        # Get relevant questions
        qa_pairs = retrieve_relevant_qa(
            query=query,
            top_k=5,
            skill=relevant_skill
        )
        
        # Extract just the questions and filter out None values
        questions = [qa['question'] for qa in qa_pairs if qa.get('question') is not None]
        
        # If we didn't get enough questions, return what we have
        if len(questions) < 3:
            print(f"Retrieved only {len(questions)} questions from RAG")
        
        return questions
    except Exception as e:
        print(f"Error retrieving RAG questions: {str(e)}")
        return []

# Add a function to identify candidate skills from resume
def extract_key_skills(skills_text):
    """
    Extract and normalize key skills from the resume skills section
    """
    # Common skills to look for
    skill_categories = {
        "python": ["python", "pandas", "numpy", "scikit-learn", "sklearn", "pytorch", "tensorflow"],
        "sql": ["sql", "mysql", "postgresql", "database", "databases", "querying"],
        "data_engineering": ["etl", "data pipeline", "data engineering", "airflow", "spark", "hadoop"],
        "machine_learning": ["machine learning", "ml", "ai", "deep learning", "nlp", "natural language processing"],
        "data_visualization": ["tableau", "power bi", "visualization", "dashboard", "matplotlib", "seaborn"],
        "cloud": ["aws", "azure", "gcp", "cloud", "s3", "ec2", "lambda"],
        "big_data": ["spark", "hadoop", "big data", "distributed computing"],
        "statistics": ["statistics", "statistical analysis", "hypothesis testing", "a/b testing"]
    }
    
    # Normalize the skills text
    skills_lower = skills_text.lower()
    
    # Find matches
    matched_skills = {}
    for category, keywords in skill_categories.items():
        for keyword in keywords:
            if keyword in skills_lower:
                if category not in matched_skills:
                    matched_skills[category] = []
                matched_skills[category].append(keyword)
    
    return matched_skills

# Add a function to identify job requirements
def extract_job_requirements(job_description):
    """
    Extract key requirements from job description
    """
    # Common requirements to look for
    requirement_categories = {
        "python": ["python", "pandas", "numpy", "scikit-learn", "sklearn", "pytorch", "tensorflow"],
        "sql": ["sql", "mysql", "postgresql", "database", "databases", "querying"],
        "data_engineering": ["etl", "data pipeline", "data engineering", "airflow", "spark", "hadoop"],
        "machine_learning": ["machine learning", "ml", "ai", "deep learning", "nlp", "natural language processing"],
        "data_visualization": ["tableau", "power bi", "visualization", "dashboard", "matplotlib", "seaborn"],
        "cloud": ["aws", "azure", "gcp", "cloud", "s3", "ec2", "lambda"],
        "big_data": ["spark", "hadoop", "big data", "distributed computing"],
        "statistics": ["statistics", "statistical analysis", "hypothesis testing", "a/b testing"]
    }
    
    # Normalize the job description
    job_lower = job_description.lower()
    
    # Find matches
    matched_requirements = {}
    for category, keywords in requirement_categories.items():
        for keyword in keywords:
            if keyword in job_lower:
                if category not in matched_requirements:
                    matched_requirements[category] = []
                matched_requirements[category].append(keyword)
    
    return matched_requirements

# Add function to determine next interview topic
def determine_next_topic(candidate_skills, job_requirements, explored_topics=None):
    """
    Determine the next topic to explore in the interview based on:
    1. Matching skills to job requirements
    2. Topics not yet explored
    3. Priority of technical areas
    """
    if explored_topics is None:
        explored_topics = []
    
    # Find matching skills and requirements
    matching_topics = set(candidate_skills.keys()) & set(job_requirements.keys())
    
    # Remove already explored topics
    available_topics = [topic for topic in matching_topics if topic not in explored_topics]
    
    # If no matching topics left, look at skills not in requirements
    if not available_topics:
        available_topics = [topic for topic in candidate_skills.keys() if topic not in explored_topics]
    
    # If still no topics, look at requirements not in skills
    if not available_topics:
        available_topics = [topic for topic in job_requirements.keys() if topic not in explored_topics]
    
    # If still no topics, use a default list of common topics
    if not available_topics:
        common_topics = ["python", "sql", "data_engineering", "machine_learning", "data_visualization", "statistics"]
        available_topics = [topic for topic in common_topics if topic not in explored_topics]
    
    # If we've explored all topics, return the first matching topic to revisit
    if not available_topics and matching_topics:
        return list(matching_topics)[0]
    elif not available_topics:
        return "general"
    
    # Return the first available topic
    return available_topics[0]

# Function to get topic-specific questions from RAG
def get_topic_questions(topic, job_description, interview_type):
    """
    Get relevant questions for a specific topic using RAG
    """
    # Map internal topic names to user-friendly names
    topic_display_names = {
        "python": "Python programming",
        "sql": "SQL and database management",
        "data_engineering": "data engineering and ETL processes",
        "machine_learning": "machine learning",
        "data_visualization": "data visualization",
        "cloud": "cloud computing",
        "big_data": "big data technologies",
        "statistics": "statistics"
    }
    
    display_name = topic_display_names.get(topic, topic)
    
    # Build query based on topic and interview type
    if interview_type.lower() == "technical":
        query = f"Technical interview questions about {display_name} for a {job_description} position"
    else:
        query = f"Behavioral interview questions about using {display_name} for a {job_description} position"
    
    try:
        # Use the retrieve_relevant_qa function to get topic-specific questions
        from query_pinecone import retrieve_relevant_qa
        
        # Get relevant questions
        qa_pairs = retrieve_relevant_qa(
            query=query,
            top_k=5,
            skill=topic if topic in ["python", "sql", "machine_learning"] else None
        )
        
        # Extract just the questions and filter out None values
        questions = [qa['question'] for qa in qa_pairs if qa.get('question') is not None]
        
        # If we didn't get enough questions, generate some
        if len(questions) < 2:
            print(f"Retrieved only {len(questions)} questions for {topic} from RAG")
            
            # Add topic-specific fallback questions based on the topic
            if topic == "python":
                questions.extend([
                    f"Could you explain how you've used Python in your data projects?",
                    f"What Python libraries do you typically use for data analysis and why?",
                    f"Can you describe a complex problem you solved using Python?"
                ])
            elif topic == "sql":
                questions.extend([
                    f"How comfortable are you with writing complex SQL queries?",
                    f"Could you explain the difference between various types of joins in SQL?",
                    f"Have you worked with database optimization? What techniques do you use?"
                ])
            elif topic == "data_engineering":
                questions.extend([
                    f"Could you describe your experience with ETL processes?",
                    f"What tools have you used for data pipeline development?",
                    f"How do you ensure data quality in your pipelines?"
                ])
            elif topic == "machine_learning":
                questions.extend([
                    f"What machine learning projects have you worked on?",
                    f"How do you approach feature selection and engineering?",
                    f"How do you evaluate the performance of your machine learning models?"
                ])
            elif topic == "data_visualization":
                questions.extend([
                    f"What visualization tools have you worked with?",
                    f"How do you choose the right visualization for different types of data?",
                    f"Can you describe a dashboard you created and the insights it provided?"
                ])
            elif topic == "cloud":
                questions.extend([
                    f"What cloud platforms have you worked with?",
                    f"How have you deployed data solutions in the cloud?",
                    f"What advantages do cloud solutions offer for data processing?"
                ])
            elif topic == "statistics":
                questions.extend([
                    f"How do you apply statistical methods in your data analysis?",
                    f"Could you explain the concept of statistical significance?",
                    f"What statistical tests do you commonly use in your work?"
                ])
            else:
                questions.extend([
                    f"Could you tell me about your experience with {display_name}?",
                    f"How have you applied your knowledge of {display_name} in your previous roles?",
                    f"What challenges have you faced when working with {display_name}?"
                ])
        
        return questions
    except Exception as e:
        print(f"Error retrieving topic questions: {str(e)}")
        return []

# Add function to generate topic transitions
def generate_topic_transition(topic, is_first_topic=False):
    """
    Generate natural transitions between interview topics
    """
    # Map internal topic names to user-friendly names
    topic_display_names = {
        "python": "Python programming",
        "sql": "SQL and database management",
        "data_engineering": "data engineering and ETL processes",
        "machine_learning": "machine learning",
        "data_visualization": "data visualization",
        "cloud": "cloud computing",
        "big_data": "big data technologies",
        "statistics": "statistics",
        "general": "general technical skills"
    }
    
    display_name = topic_display_names.get(topic, topic)
    
    # Initial topic introduction
    if is_first_topic:
        transitions = [
            f"Let's start by discussing your experience with {display_name}.",
            f"I'd like to begin by exploring your knowledge of {display_name}.",
            f"To start off, I'd like to ask you about your experience with {display_name}.",
            f"Let's dive into your background with {display_name} first."
        ]
    # Transitions to subsequent topics
    else:
        transitions = [
            f"Great. Now let's move on to discuss your experience with {display_name}.",
            f"Thank you for that. I'd like to switch gears and talk about your knowledge of {display_name}.",
            f"That's helpful information. Let's now explore your skills in {display_name}.",
            f"I appreciate those insights. Let's shift our focus to {display_name}.",
            f"Excellent. I'd like to move on to another area. Could you tell me about your experience with {display_name}?"
        ]
    
    # Return a random transition phrase
    return random.choice(transitions)

# Add function to store and retrieve session state
def get_session_state(user_id):
    """
    Retrieve the current interview session state for a user
    """
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    
    # Create table if it doesn't exist
    c.execute('''
    CREATE TABLE IF NOT EXISTS interview_session (
        user_id INTEGER PRIMARY KEY,
        state TEXT
    )
    ''')
    
    # Try to get existing state
    c.execute("SELECT state FROM interview_session WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    
    if result:
        # Parse stored JSON state
        state_dict = json.loads(result[0])
        state = InterviewSessionState(**state_dict)
    else:
        # Create new state
        state = InterviewSessionState()
    
    conn.close()
    return state

def save_session_state(user_id, state):
    """
    Save the interview session state for a user
    """
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    
    # Ensure table exists
    c.execute('''
    CREATE TABLE IF NOT EXISTS interview_session (
        user_id INTEGER PRIMARY KEY,
        state TEXT
    )
    ''')
    
    # Store state as JSON
    state_json = json.dumps(state.dict())
    
    # Insert or update state
    c.execute(
        "INSERT OR REPLACE INTO interview_session (user_id, state) VALUES (?, ?)",
        (user_id, state_json)
    )
    
    conn.commit()
    conn.close()

# Add function to extract concepts from topics based on job description and skills
def extract_topic_concepts(topic, job_description, skills):
    """
    Extract key concepts for a specific topic based on job description and skills
    """
    # Define common concepts for each topic area
    topic_concepts = {
        "python": [
            "data structures", "pandas", "numpy", "list comprehensions", 
            "object-oriented programming", "decorators", "generators",
            "error handling", "file handling", "libraries", "frameworks"
        ],
        "sql": [
            "joins", "subqueries", "indexes", "optimization", "window functions",
            "normalization", "data modeling", "transactions", "views", "stored procedures"
        ],
        "data_engineering": [
            "etl processes", "data pipelines", "batch vs streaming", "data warehousing",
            "data lake", "data governance", "data quality", "data partitioning",
            "distributed computing", "workflow orchestration"
        ],
        "machine_learning": [
            "supervised learning", "unsupervised learning", "feature engineering",
            "model evaluation", "overfitting", "underfitting", "cross-validation",
            "neural networks", "decision trees", "classification", "regression"
        ],
        "data_visualization": [
            "chart types", "dashboarding", "bi tools", "visual design principles",
            "interactive visualizations", "storytelling with data", "reporting"
        ],
        "cloud": [
            "service models", "deployment models", "storage solutions", "compute services",
            "serverless", "containers", "kubernetes", "infrastructure as code", "cost optimization"
        ],
        "big_data": [
            "hadoop", "spark", "distributed systems", "parallel processing",
            "data partitioning", "scaling strategies", "real-time processing"
        ],
        "statistics": [
            "hypothesis testing", "probability distributions", "sampling methods",
            "confidence intervals", "regression analysis", "experimental design",
            "a/b testing", "statistical significance", "correlation vs causation"
        ],
        "general": [
            "problem solving", "communication", "teamwork", "project management",
            "time management", "technical documentation", "best practices"
        ]
    }
    
    # Get default concepts for the topic
    default_concepts = topic_concepts.get(topic, ["general knowledge", "fundamentals", "best practices"])
    
    # Normalize text for search
    job_desc_lower = job_description.lower()
    skills_lower = skills.lower()
    
    # Find concepts that appear in job description or skills
    relevant_concepts = []
    for concept in default_concepts:
        if concept in job_desc_lower or concept in skills_lower:
            relevant_concepts.append(concept)
    
    # Always include at least 3 concepts
    if len(relevant_concepts) < 3:
        # Add concepts until we have at least 3
        for concept in default_concepts:
            if concept not in relevant_concepts:
                relevant_concepts.append(concept)
            if len(relevant_concepts) >= 3:
                break
    
    return relevant_concepts

# Add function to generate behavioral questions for different topics
def generate_behavioral_questions(topic, concept=None, tech_terms=None):
    """
    Generate behavioral interview questions related to the given topic and concept.
    These questions focus on past experiences, teamwork, and soft skills.
    """
    # Initialize list for questions
    questions = []
    
    # Common behavioral question templates by topic
    if topic == "python" or topic == "sql" or topic == "machine_learning" or "data" in topic:
        # Technical experience behavioral questions
        questions.extend([
            f"Tell me about a challenging project where you applied your {topic} skills. What was your role and how did you overcome obstacles?",
            f"Describe a situation where you had to learn a new {topic} technology or framework quickly. How did you approach it?",
            f"Can you share an experience where you had to debug a complex issue related to {topic}? What was your process?",
            f"Tell me about a time when you improved the performance or efficiency of a {topic} solution. What was your approach?",
            f"Have you ever had to explain complex {topic} concepts to non-technical stakeholders? How did you approach this?"
        ])
    
    # Add concept-specific questions if a concept is provided
    if concept:
        concept_questions = [
            f"Describe a project where you applied {concept} in your work. What challenges did you face?",
            f"Tell me about a time when you had to make a difficult decision related to {concept}. What factors did you consider?",
            f"Have you ever had to collaborate with others on implementing {concept}? How did you ensure effective teamwork?",
            f"Share an experience where you had to adapt your approach to {concept} based on changing requirements.",
            f"Can you describe a situation where you had to advocate for using {concept} when others preferred a different approach?"
        ]
        questions.extend(concept_questions)
    
    # Add technology-specific behavioral questions
    if tech_terms:
        for term in tech_terms[:2]:  # Limit to first 2 terms to avoid too many questions
            tech_questions = [
                f"Tell me about your experience using {term}. What projects have you applied it to?",
                f"Describe a challenge you faced when working with {term} and how you overcame it.",
                f"Have you ever had to teach or mentor someone on {term}? What approach did you take?"
            ]
            questions.extend(tech_questions)
    
    # Add some general behavioral questions for data professionals
    general_data_questions = [
        "Tell me about a time when you had to work with incomplete or messy data. How did you handle it?",
        "Describe a situation where you had to balance data quality with tight deadlines. What tradeoffs did you make?",
        "Can you share an experience where you helped drive a data-informed decision that had significant impact?",
        "Tell me about a time when you had to present complex analysis results to stakeholders. How did you make it understandable?",
        "Describe a situation where you identified an opportunity for process improvement through data analysis."
    ]
    questions.extend(general_data_questions)
    
    # Return a subset of questions to avoid overwhelming
    if len(questions) > 5:
        # Shuffle and pick 5 questions
        random.shuffle(questions)
        return questions[:5]
    
    return questions

# Modify the get_concept_questions function to properly handle behavioral questions
def get_concept_questions(topic, concept, difficulty, job_description, interview_type, user_skills=""):
    """
    Get questions for a specific concept within a topic at the specified difficulty level
    with added context from resume and job description for more targeted questions.
    """
    # Add debug logging
    print(f"get_concept_questions called with interview_type: '{interview_type}' (type: {type(interview_type)})")
    print(f"Parameters: topic='{topic}', concept='{concept}', difficulty='{difficulty}'")
    
    # Convert interview_type to lowercase to simplify comparisons
    interview_type_lower = interview_type.lower() if isinstance(interview_type, str) else "technical"
    
    # For behavioral interviews, use a different approach focused on experiences and soft skills
    if interview_type_lower == "behavioral":
        print(f"Using BEHAVIORAL question generation path for topic: '{topic}', concept: '{concept}'")
        
        # Extract relevant technical terms from job description and skills
        job_desc_lower = job_description.lower()
        user_skills_lower = user_skills.lower() if user_skills else ""
        
        tech_terms = []
        common_tech_terms = ["python", "java", "javascript", "react", "angular", "vue", "node.js", 
                            "express", "django", "flask", "fastapi", "sql", "nosql", "mongodb", 
                            "postgresql", "mysql", "oracle", "aws", "azure", "gcp", "docker", 
                            "kubernetes", "terraform", "ci/cd", "git", "github", "bitbucket", 
                            "machine learning", "deep learning", "tensorflow", "pytorch", "pandas", 
                            "numpy", "scikit-learn", "data engineering", "etl", "airflow", "spark"]
        
        # First check user skills for technologies
        for term in common_tech_terms:
            if user_skills_lower and term in user_skills_lower:
                tech_terms.append(term)
        
        # Then check job description if we need more terms
        if len(tech_terms) < 3:
            for term in common_tech_terms:
                if term in job_desc_lower and term not in tech_terms:
                    tech_terms.append(term)
                    if len(tech_terms) >= 3:
                        break
        
        # Build the behavioral query for RAG
        tech_context = ", ".join(tech_terms[:3]) if tech_terms else "relevant technologies"
        query = f"behavioral interview questions about {concept} in {topic} for a {job_description} position involving {tech_context}"
        
        try:
            # Try to get behavioral questions from RAG first
            from query_pinecone import retrieve_relevant_qa
            
            # Get relevant questions for behavioral
            qa_pairs = retrieve_relevant_qa(
                query=query,
                top_k=5,
                skill=topic if topic in ["python", "sql", "machine_learning"] else None
            )
            
            # Extract just the questions and filter out None values
            questions = [qa['question'] for qa in qa_pairs if qa.get('question') is not None]
            
            # If we don't have enough questions from RAG, use our behavioral question generator
            if len(questions) < 3:
                print(f"Retrieved only {len(questions)} behavioral questions for {concept} in {topic} from RAG")
                
                # Generate behavioral questions using our custom function
                try:
                    behavioral_questions = generate_behavioral_questions(topic, concept, tech_terms)
                    print(f"Generated {len(behavioral_questions)} additional behavioral questions")
                    questions.extend(behavioral_questions)
                except Exception as bq_error:
                    print(f"Error generating behavioral questions: {str(bq_error)}")
                    print(traceback.format_exc())
                    # Fallback to some generic behavioral questions
                    questions.extend([
                        "Could you tell me about a challenging project you worked on and how you overcame obstacles?",
                        "Describe a situation where you had to learn something new quickly. How did you approach it?",
                        "Tell me about a time when you had to work with a difficult team member. How did you handle it?"
                    ])
            
            return questions
        except Exception as e:
            print(f"Error retrieving behavioral questions: {str(e)}")
            print(traceback.format_exc())
            return generate_behavioral_questions(topic, concept, tech_terms)
    
    # For technical interviews, continue with the existing approach
    else:
        # For technical interviews, continue with the existing approach
        print(f"Using TECHNICAL question generation path for topic: '{topic}', concept: '{concept}'")
        
        # Map difficulty to more specific terms for the query
        difficulty_terms = {
            "easy": "basic",
            "medium": "intermediate",
            "hard": "advanced"
        }
        
        difficulty_term = difficulty_terms.get(difficulty, "intermediate")
        
        # Extract relevant technical terms from job description
        job_desc_lower = job_description.lower()
        user_skills_lower = user_skills.lower() if user_skills else ""
        
        tech_terms = []
        common_tech_terms = ["python", "java", "javascript", "react", "angular", "vue", "node.js", 
                            "express", "django", "flask", "fastapi", "sql", "nosql", "mongodb", 
                            "postgresql", "mysql", "oracle", "aws", "azure", "gcp", "docker", 
                            "kubernetes", "terraform", "ci/cd", "git", "github", "bitbucket", 
                            "machine learning", "deep learning", "tensorflow", "pytorch", "pandas", 
                            "numpy", "scikit-learn", "data engineering", "etl", "airflow", "spark"]
        
        # First check user skills for technologies
        for term in common_tech_terms:
            if user_skills_lower and term in user_skills_lower:
                tech_terms.append(term)
        
        # Then check job description if we need more terms
        if len(tech_terms) < 3:
            for term in common_tech_terms:
                if term in job_desc_lower and term not in tech_terms:
                    tech_terms.append(term)
                    if len(tech_terms) >= 3:
                        break
        
        # Build a specific query for RAG that includes technical context
        tech_context = ", ".join(tech_terms[:3]) if tech_terms else "relevant technologies"
        
        # Create a more specific query using extracted technical terms
        query = f"{difficulty_term} technical interview questions about {concept} in {topic} for a {job_description} position using {tech_context}"
        
        try:
            # Use the retrieve_relevant_qa function to get concept-specific questions
            from query_pinecone import retrieve_relevant_qa
            
            # Get relevant questions with higher top_k to ensure we get enough good questions
            qa_pairs = retrieve_relevant_qa(
                query=query,
                top_k=5,
                skill=topic if topic in ["python", "sql", "machine_learning"] else None
            )
            
            # Extract just the questions and filter out None values
            questions = [qa['question'] for qa in qa_pairs if qa.get('question') is not None]
            
            # If we didn't get enough questions, generate some
            if len(questions) < 2:
                print(f"Retrieved only {len(questions)} {difficulty} questions for {concept} in {topic} from RAG")
                
                # Generate fallback questions based on concept and difficulty with context
                generated_questions = generate_concept_questions(topic, concept, difficulty, tech_terms)
                questions.extend(generated_questions)
            
            return questions
        except Exception as e:
            print(f"Error retrieving concept questions: {str(e)}")
            return generate_concept_questions(topic, concept, difficulty, tech_terms)

# Generate fallback questions for concepts based on difficulty
def generate_concept_questions(topic, concept, difficulty, tech_terms=None):
    """
    Generate questions for a concept within a topic at different difficulty levels
    with added context from resume and job description for more targeted questions.
    """
    questions = []
    
    # Common programming/technical terms to check for specific question templates
    if not tech_terms:
        tech_terms = []
    
    # Python concept questions
    if topic == "python":
        if concept == "data structures":
            if difficulty == "easy":
                questions.append(f"What are the main data structures in Python and when would you use each one?")
                questions.append(f"Could you explain the difference between lists and tuples in Python?")
            elif difficulty == "medium":
                questions.append(f"Can you explain the performance differences between lists and dictionaries in Python?")
                questions.append(f"How would you implement a custom data structure for an LRU cache in Python?")
            else:  # hard
                questions.append(f"How would you implement a memory-efficient data structure for a large dataset in Python?")
                questions.append(f"Could you describe how you would implement a custom B-tree in Python and when you would use it?")
        
        elif concept == "pandas":
            if difficulty == "easy":
                questions.append(f"What are the core data structures in pandas and what are they used for?")
                questions.append(f"How do you handle missing data in pandas?")
            elif difficulty == "medium":
                questions.append(f"Could you explain the concept of vectorization in pandas and why it's important for performance?")
                questions.append(f"How would you optimize pandas operations when working with large datasets?")
            else:  # hard
                questions.append(f"Can you explain how you would implement a custom pandas extension array for specialized data?")
                questions.append(f"What strategies would you use to parallelize pandas operations for multi-core processing?")
        
        elif concept == "object-oriented programming":
            if difficulty == "easy":
                questions.append(f"Could you explain the basic principles of OOP in Python?")
                questions.append(f"What are class methods, instance methods, and static methods in Python?")
            elif difficulty == "medium":
                questions.append(f"How would you implement inheritance and method overriding in Python?")
                questions.append(f"Can you explain metaclasses in Python and provide a practical example?")
            else:  # hard
                questions.append(f"Could you explain the descriptor protocol in Python and when you would use it?")
                questions.append(f"How would you implement a custom context manager in Python?")
    
    # SQL concept questions
    elif topic == "sql":
        if concept == "joins":
            if difficulty == "easy":
                questions.append(f"Could you explain the different types of joins in SQL?")
                questions.append(f"When would you use a LEFT JOIN versus an INNER JOIN?")
            elif difficulty == "medium":
                questions.append(f"When would you use a self join, and can you provide an example?")
                questions.append(f"How would you implement a hierarchical query using recursive CTEs?")
            else:  # hard
                questions.append(f"How would you optimize a query that involves multiple joins on large tables?")
                questions.append(f"Can you explain how you would implement a dynamic pivot in SQL?")
        
        elif concept == "optimization":
            if difficulty == "easy":
                questions.append(f"What are indexes in SQL and why are they important?")
                questions.append(f"How do you identify slow-performing SQL queries?")
            elif difficulty == "medium":
                questions.append(f"Could you explain how to optimize subqueries in SQL?")
                questions.append(f"What approaches would you use to optimize aggregate functions in SQL?")
            else:  # hard
                questions.append(f"Can you discuss strategies for optimizing complex analytical queries on large datasets?")
                questions.append(f"How would you approach query optimization when dealing with partitioned tables?")
    
    # Data engineering concept questions
    elif topic == "data_engineering":
        if concept == "etl processes":
            if difficulty == "easy":
                questions.append(f"What are ETL processes and why are they important in data engineering?")
                questions.append(f"Could you explain the difference between batch and streaming ETL?")
            elif difficulty == "medium":
                questions.append(f"How would you design an ETL pipeline for handling late-arriving data?")
                questions.append(f"What strategies would you use to monitor and ensure data quality in ETL pipelines?")
            else:  # hard
                questions.append(f"Could you describe how you would implement a fault-tolerant, scalable ETL system?")
                questions.append(f"How would you approach the migration of a legacy ETL system to a modern data architecture?")
        
        elif concept == "data pipelines":
            if difficulty == "easy":
                questions.append(f"What are the key components of a data pipeline?")
                questions.append(f"How do you ensure data quality in a pipeline?")
            elif difficulty == "medium":
                questions.append(f"Could you explain how you would implement incremental data loading in a pipeline?")
                questions.append(f"What approaches would you use for error handling and recovery in data pipelines?")
            else:  # hard
                questions.append(f"How would you design a data pipeline that requires both real-time and batch processing?")
                questions.append(f"Can you explain how you would implement a multi-tenant data pipeline with different SLAs?")
    
    # Machine learning concept questions
    elif topic == "machine_learning":
        if concept == "feature engineering":
            if difficulty == "easy":
                questions.append(f"What is feature engineering and why is it important in machine learning?")
                questions.append(f"What are some common techniques for handling categorical variables?")
            elif difficulty == "medium":
                questions.append(f"Can you explain different approaches to handling imbalanced data in machine learning?")
                questions.append(f"How would you approach feature selection for a high-dimensional dataset?")
            else:  # hard
                questions.append(f"How would you design a feature engineering pipeline for time series data?")
                questions.append(f"Could you explain techniques for automated feature engineering and when you would use them?")
        
        elif concept == "model evaluation":
            if difficulty == "easy":
                questions.append(f"What metrics would you use to evaluate a classification model versus a regression model?")
                questions.append(f"Can you explain the concept of cross-validation?")
            elif difficulty == "medium":
                questions.append(f"How do you address the issue of class imbalance when evaluating a model?")
                questions.append(f"What approaches would you use to detect and handle overfitting?")
            else:  # hard
                questions.append(f"Can you explain how you would implement a custom evaluation metric for a specific business problem?")
                questions.append(f"How would you approach model evaluation in an online learning setting?")
    
    # Cloud computing questions
    elif topic == "cloud":
        if concept == "aws":
            if difficulty == "easy":
                questions.append(f"What are the main AWS services you've worked with for data processing?")
                questions.append(f"Could you explain the difference between S3, EBS, and EFS storage options?")
            elif difficulty == "medium":
                questions.append(f"How would you design a serverless data processing pipeline on AWS?")
                questions.append(f"What AWS services would you use for a real-time analytics system?")
            else:  # hard
                questions.append(f"Could you describe how you would implement a cost-optimized, multi-region data architecture on AWS?")
                questions.append(f"How would you approach security and compliance for a large-scale data lake on AWS?")
        
        elif concept == "containers":
            if difficulty == "easy":
                questions.append(f"What are containers and how do they differ from virtual machines?")
                questions.append(f"Could you explain the key components of Docker?")
            elif difficulty == "medium":
                questions.append(f"How would you design a containerized microservices architecture?")
                questions.append(f"What approaches would you use for container orchestration?")
            else:  # hard
                questions.append(f"Could you explain how you would implement a security-focused container strategy?")
                questions.append(f"How would you design a CI/CD pipeline for containerized applications?")
    
    # Generate behavioral questions if no specific ones are defined or for non-technical topics
    if not questions or topic == "behavioral":
        # Behavioral questions based on topic
        behavioral_questions = [
            f"Tell me about a challenging project where you applied your {topic} skills. What was your role and how did you overcome obstacles?",
            f"Describe a situation where you had to learn a new {topic} technology or framework quickly. How did you approach it?",
            f"Can you share an experience where you had to debug a complex issue related to {topic}? What was your process?",
            f"Tell me about a time when you improved the performance or efficiency of a {topic} solution. What was your approach?",
            f"Have you ever had to explain complex {topic} concepts to non-technical stakeholders? How did you approach this?"
        ]
        
        # Concept-specific behavioral questions
        if concept:
            behavioral_questions.extend([
                f"Describe a project where you applied {concept} in your work. What challenges did you face?",
                f"Tell me about a time when you had to make a difficult decision related to {concept}. What factors did you consider?",
                f"Have you ever had to collaborate with others on implementing {concept}? How did you ensure effective teamwork?",
                f"Share an experience where you had to adapt your approach to {concept} based on changing requirements."
            ])
        
        # General behavioral questions for data professionals
        general_questions = [
            "Tell me about a time when you had to work with incomplete or messy data. How did you handle it?",
            "Describe a situation where you had to balance data quality with tight deadlines. What tradeoffs did you make?",
            "Can you share an experience where you helped drive a data-informed decision that had significant impact?",
            "Tell me about a time when you had to present complex analysis results to stakeholders. How did you make it understandable?"
        ]
        
        # Combine all behavioral questions
        questions.extend(behavioral_questions)
        questions.extend(general_questions)
    
    # If we have too many questions, select a subset based on difficulty
    if len(questions) > 5:
        # For harder difficulty, take the latter questions which tend to be more complex
        if difficulty == "hard":
            return questions[-5:]
        # For easier difficulty, take the first questions which tend to be more straightforward
        elif difficulty == "easy":
            return questions[:5]
        # For medium difficulty, take from the middle
        else:
            middle = len(questions) // 2
            return questions[middle-2:middle+3]
    
    return questions

# Add function to generate natural feedback responses
def generate_answer_feedback(answer_length=0, contains_technical_terms=False):
    """
    Generate a natural, positive feedback response after an answer
    """
    # Simple feedback phrases
    simple_feedback = [
        "That's a good point.",
        "I see, thanks for sharing that.",
        "That makes sense.",
        "Interesting perspective.",
        "Thanks for explaining that.",
        "I appreciate your answer.",
        "That's helpful information.",
        "Good to know.",
        "Thanks for sharing your approach."
    ]
    
    # More specific feedback based on answer characteristics
    technical_feedback = [
        "That's a solid technical explanation.",
        "Your technical knowledge is evident.",
        "That's a well-articulated technical response.",
        "I appreciate your detailed technical explanation.",
        "Good technical insight there."
    ]
    
    detailed_feedback = [
        "Thanks for the comprehensive answer.",
        "I appreciate that detailed explanation.",
        "That's quite thorough, thank you.",
        "Thanks for providing such a detailed response.",
        "That's a well-elaborated answer."
    ]
    
    # Select appropriate feedback based on answer characteristics
    if contains_technical_terms and answer_length > 100:
        candidates = technical_feedback + detailed_feedback
    elif contains_technical_terms:
        candidates = technical_feedback + simple_feedback
    elif answer_length > 100:
        candidates = detailed_feedback + simple_feedback
    else:
        candidates = simple_feedback
    
    # Return a random feedback phrase
    return random.choice(candidates)

def evaluate_answer_quality(answer, context=None):
    """
    Evaluate the quality of a user's answer and determine if follow-up is needed.
    Returns:
    - is_short: Whether the answer is too short or lacks detail
    - is_vague: Whether the answer is vague or generic
    - follow_up_question: A follow-up question if needed, or None if not
    - feedback: Appropriate feedback based on answer quality
    """
    answer_length = len(answer)
    words = answer.split()
    word_count = len(words)
    
    # Check for short answers
    is_short = word_count < 15 or answer_length < 80
    
    # Check for one-word or very short answers
    is_very_short = word_count < 5
    
    # Check for vague/generic answers
    generic_phrases = ["yes", "no", "maybe", "i don't know", "not sure", "i guess", "ok", "okay"]
    is_vague = any(phrase == answer.lower() for phrase in generic_phrases) or (
        word_count < 10 and not any(char in answer for char in ",.;:!?")
    )
    
    # Generate appropriate feedback based on quality
    if is_very_short:
        feedback_options = [
            "I'd like to hear more about that.",
            "Could you elaborate on that?",
            "I'd appreciate if you could share more details.",
            "Let's explore that further.",
            "I'm interested in learning more about your perspective."
        ]
    elif is_short:
        feedback_options = [
            "Thanks for sharing that.",
            "I see.",
            "That's interesting.",
            "I appreciate your answer.",
            "Thank you for that response."
        ]
    else:
        # For sufficient answers, use the regular feedback generator
        return False, False, None, None
    
    feedback = random.choice(feedback_options)
    
    # Generate follow-up questions for insufficient answers
    if is_very_short or is_vague:
        if context and 'topic' in context:
            topic = context['topic']
            concept = context.get('concept')
            
            if concept:
                follow_up_options = [
                    f"Could you explain more about your experience with {concept} in {topic}?",
                    f"What specific aspects of {concept} have you worked with?",
                    f"Can you provide an example of how you've applied {concept}?",
                    f"What challenges have you faced when working with {concept}?",
                    f"How would you explain {concept} to someone new to {topic}?"
                ]
            else:
                follow_up_options = [
                    f"Could you share more about your experience with {topic}?",
                    f"What specific projects have you worked on that involved {topic}?",
                    f"What aspects of {topic} are you most familiar with?",
                    f"How have you applied your knowledge of {topic} in your work?",
                    f"What do you find most interesting about {topic}?"
                ]
        else:
            # Generic follow-up questions when no context is available
            follow_up_options = [
                "Could you elaborate on that with some specific examples?",
                "Can you tell me more about your experience in this area?",
                "What specific skills or approaches have you used?",
                "Could you walk me through a scenario where you applied this?",
                "What particular aspects have you found most challenging or interesting?"
            ]
        
        follow_up_question = random.choice(follow_up_options)
        return is_short, is_vague, follow_up_question, feedback
    
    return is_short, is_vague, None, feedback

# Function to generate personalized introduction acknowledgment
def generate_introduction_acknowledgment(intro_message):
    """
    Generate a personalized acknowledgment of the candidate's introduction
    before transitioning to the first technical question.
    """
    # Extract potential background information from the introduction
    has_experience = any(term in intro_message.lower() for term in 
                        ["experience", "worked", "background", "years", "job", "role", 
                         "position", "project", "developed", "built", "created", "degree"])
    
    has_education = any(term in intro_message.lower() for term in 
                       ["university", "college", "degree", "graduated", "school", 
                        "bachelor", "master", "phd", "student", "studying"])
    
    has_interests = any(term in intro_message.lower() for term in 
                       ["interested", "passion", "enjoy", "love", "excited", "hobby", 
                        "focus", "specialized", "specializing", "learning"])
    
    # Generate appropriate acknowledgment
    acknowledgments = []
    
    if has_experience:
        experience_acks = [
            "Thanks for sharing your professional background.",
            "I appreciate you walking me through your experience.",
            "Your experience sounds relevant for the role we're discussing.",
            "Thanks for sharing those details about your work history."
        ]
        acknowledgments.append(random.choice(experience_acks))
    
    if has_education:
        education_acks = [
            "Thanks for sharing your educational background.",
            "Your academic background provides good context.",
            "I appreciate knowing about your educational journey.",
            "That's helpful to know about your studies."
        ]
        acknowledgments.append(random.choice(education_acks))
    
    if has_interests:
        interest_acks = [
            "I can see your enthusiasm for this field.",
            "Your interests align well with what we're looking for.",
            "It's great to hear about your passion in these areas.",
            "Thanks for sharing what motivates you in your work."
        ]
        acknowledgments.append(random.choice(interest_acks))
    
    # If we couldn't detect any specific elements, use a generic acknowledgment
    if not acknowledgments:
        generic_acks = [
            "Thank you for that introduction.",
            "Thanks for sharing a bit about yourself.",
            "I appreciate you taking the time to introduce yourself.",
            "That gives me a better understanding of your background."
        ]
        acknowledgments.append(random.choice(generic_acks))
    
    # Add a transitional phrase
    transitions = [
        "Now, I'd like to move on to some questions about your technical experience.",
        "Let's dive into some specific technical areas relevant to the role.",
        "I'd like to learn more about your technical skills and expertise.",
        "Now, let's focus on some technical aspects related to this position."
    ]
    
    # Combine acknowledgment and transition
    if len(acknowledgments) > 1:
        # If we have multiple acknowledgments, use just the first one to keep it concise
        acknowledgment = acknowledgments[0]
    else:
        acknowledgment = acknowledgments[0]
    
    return f"{acknowledgment} {random.choice(transitions)}"

# Add function to detect if the candidate wants to end the interview
def detect_end_interview_request(message):
    """
    Detect if the candidate's message indicates they want to end the interview
    """
    # Common phrases indicating a desire to end the interview
    end_phrases = [
        "i would like to end",
        "can we end",
        "let's end",
        "i think we can end",
        "i think we should end", 
        "we can end",
        "we should end",
        "want to end",
        "i am done",
        "i'm done",
        "that's all",
        "that is all",
        "finish the interview",
        "conclude the interview",
        "let's wrap up",
        "let's finish",
        "wrap up the interview",
        "complete the interview",
        "end this interview",
        "end the interview",
        "don't have more questions"
        "no more questions"
    ]
    
    # Check if any end phrase is in the message
    message_lower = message.lower()
    for phrase in end_phrases:
        if phrase in message_lower:
            return True
    
    return False

# Add function to extract relevant technologies from the resume
def extract_resume_technologies(resume_skills, resume_experience=""):
    """
    Extract specific technologies mentioned in the resume for more targeted questions.
    
    Args:
        resume_skills: String containing skills section from resume
        resume_experience: Optional string containing work experience from resume
    
    Returns:
        dict: Categorized dictionary of technologies found in the resume
    """
    # Combine skills and experience for more comprehensive scanning
    resume_text = f"{resume_skills} {resume_experience}".lower()
    
    # Define technology categories and their keywords
    tech_categories = {
        "languages": {
            "python": ["python", "py", "pytest"],
            "java": ["java", "j2ee", "spring", "hibernate"],
            "javascript": ["javascript", "js", "typescript", "ts", "node.js", "nodejs"],
            "c++": ["c++", "cpp", "stl"],
            "c#": ["c#", "csharp", ".net", "asp.net"],
            "go": ["golang", "go lang"],
            "r": [" r ", "rstudio", "tidyverse"],
            "scala": ["scala", "spark scala"],
            "rust": ["rust", "rustlang"],
            "php": ["php", "laravel", "symfony"]
        },
        "databases": {
            "sql": ["sql", "database", "rdbms"],
            "mysql": ["mysql", "mariadb"],
            "postgresql": ["postgres", "postgresql", "psql"],
            "oracle": ["oracle", "plsql", "pl/sql"],
            "mongodb": ["mongo", "mongodb", "nosql", "document db"],
            "cassandra": ["cassandra"],
            "redis": ["redis", "in-memory db"],
            "dynamodb": ["dynamodb", "dynamo"],
            "elasticsearch": ["elasticsearch", "elk"]
        },
        "cloud": {
            "aws": ["aws", "amazon web services", "ec2", "s3", "lambda", "dynamodb", "rds"],
            "azure": ["azure", "microsoft azure", "azure functions"],
            "gcp": ["gcp", "google cloud", "bigquery"],
            "kubernetes": ["kubernetes", "k8s"],
            "docker": ["docker", "containerization"],
            "terraform": ["terraform", "infrastructure as code", "iac"]
        },
        "data_engineering": {
            "spark": ["spark", "pyspark", "databricks"],
            "hadoop": ["hadoop", "hdfs", "mapreduce"],
            "airflow": ["airflow", "dag"],
            "kafka": ["kafka", "event streaming"],
            "etl": ["etl", "extract transform load", "data pipeline"],
            "dbt": ["dbt", "data build tool"],
            "snowflake": ["snowflake"],
            "redshift": ["redshift", "amazon redshift"]
        },
        "ml_ai": {
            "machine_learning": ["machine learning", "ml", "ai", "artificial intelligence"],
            "deep_learning": ["deep learning", "neural network", "cnn", "rnn", "lstm"],
            "nlp": ["nlp", "natural language processing", "text mining"],
            "tensorflow": ["tensorflow", "tf", "keras"],
            "pytorch": ["pytorch", "torch"],
            "scikit-learn": ["scikit-learn", "sklearn"],
            "computer_vision": ["computer vision", "image recognition", "object detection"]
        },
        "data_analysis": {
            "pandas": ["pandas", "dataframe"],
            "numpy": ["numpy", "ndarray"],
            "tableau": ["tableau"],
            "power_bi": ["power bi", "powerbi"],
            "excel": ["excel", "spreadsheet", "vlookup"],
            "data_visualization": ["data visualization", "visualization", "matplotlib", "seaborn", "plotly"]
        },
        "web_development": {
            "react": ["react", "reactjs", "react.js"],
            "angular": ["angular", "angularjs"],
            "vue": ["vue", "vuejs", "vue.js"],
            "django": ["django"],
            "flask": ["flask"],
            "fastapi": ["fastapi"],
            "express": ["express", "expressjs", "express.js"]
        }
    }
    
    # Find matches in the resume
    found_technologies = {}
    
    for category, techs in tech_categories.items():
        for tech_name, keywords in techs.items():
            for keyword in keywords:
                # Use word boundary checks to avoid partial matches
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, resume_text):
                    if category not in found_technologies:
                        found_technologies[category] = []
                    if tech_name not in found_technologies[category]:
                        found_technologies[category].append(tech_name)
    
    return found_technologies

# API endpoints
@app.get("/")
async def root():
    return {"message": "AI Mock Interview API v1.0"}

@app.post("/api/register")
async def register(user: UserLogin):
    success, user_id, message = create_user(user.username, user.password)
    return UserResponse(
        user_id=user_id,
        username=user.username,
        success=success,
        message=message
    )

@app.post("/api/login")
async def login(user: UserLogin):
    success, user_id, message = login_user(user.username, user.password)
    return UserResponse(
        user_id=user_id,
        username=user.username,
        success=success,
        message=message
    )

@app.post("/api/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...),
    user_id: int = Form(...)
):
    file_content = await file.read()
    resume_text = extract_text_from_file(file_content, file.filename)
    
    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="No text found in the resume")
    
    details = extract_resume_details(resume_text)
    
    # Generate user info
    user_info = generate_user_info(resume_text, job_description)
    
    # Store in database
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO resumes (user_id, job_description, resume_filename, name, skills, work_experience, projects) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, job_description, file.filename, details["NAME"], details["SKILLS"], details["WORK_EXPERIENCE"], details["PROJECTS"])
    )
    conn.commit()
    conn.close()
    
    return {"success": True, "details": details, "user_info": user_info}

@app.post("/api/start-interview")
async def start_interview(setup: InterviewSetup):
    try:
        # Debug the incoming request
        print(f"Received interview setup request with interview_type: '{setup.interview_type}'")
        print(f"Full setup data: {setup}")
        
        # Get resume data from database
        conn = sqlite3.connect("app.db")
        c = conn.cursor()
        c.execute("SELECT resume_filename, job_description, name, skills FROM resumes WHERE user_id = ? ORDER BY id DESC LIMIT 1", (setup.user_id,))
        result = c.fetchone()
        conn.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="No resume found for this user")
        
        resume_filename, stored_job_desc, candidate_name, skills = result
        
        # Use the job description provided from the frontend
        job_description = setup.job_description if setup.job_description else stored_job_desc
        
        # Store interview type with user data
        conn = sqlite3.connect("app.db")
        c = conn.cursor()
        print(f"About to store interview type: '{setup.interview_type}' (type: {type(setup.interview_type)}) for user {setup.user_id}")
        c.execute("INSERT OR REPLACE INTO user_preferences (user_id, interview_type) VALUES (?, ?)",
                 (setup.user_id, setup.interview_type))
        conn.commit()

        # Verify it was stored correctly
        c.execute("SELECT interview_type FROM user_preferences WHERE user_id = ?", (setup.user_id,))
        stored_type = c.fetchone()
        print(f"Verified stored interview type: {stored_type}")
        conn.close()
        
        # Initialize interview session state
        initial_state = InterviewSessionState()
        save_session_state(setup.user_id, initial_state)
        
        # Clear previous conversation
        clear_conversation()
        
        # Generate personalized greeting
        initial_question = generate_personalized_greeting(candidate_name)
        
        # Save the initial question to the conversation history
        save_conversation([{"question": initial_question, "answer": ""}])
        
        return {
            "success": True, 
            "message": "Interview started", 
            "question": initial_question
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat(message: InterviewMessage):
    try:
        # Check if the candidate wants to end the interview
        if detect_end_interview_request(message.message):
            # Return a closing response
            closing_responses = [
                "Thank you for your time today. I've learned a lot about your background and skills. The interview is now complete, and you'll be redirected to the feedback page.",
                "Great! We've covered quite a bit today. Thank you for sharing your experience and knowledge. We'll now wrap up the interview and move to the feedback.",
                "Thanks for this discussion. I appreciate your detailed responses. We'll conclude the interview now and proceed to the feedback section.",
                "That concludes our interview for today. Thank you for your thoughtful answers. You'll now be directed to the feedback page."
            ]
            closing_message = random.choice(closing_responses)
            
            # Return with a special flag indicating the interview should end
            return {
                "response": closing_message,
                "end_interview": True
            }
        
        # Load conversation history
        conversation_history = load_conversation()
        
        # Get user's session state
        session_state = get_session_state(message.user_id)
        
        # Add the user's message to conversation history
        if conversation_history:
            last_question = conversation_history[-1].get("question", "")
        else:
            last_question = "Could you tell me about yourself and your background?"
            
        conversation_history.append({"question": last_question, "answer": message.message})
        save_conversation(conversation_history)
        
        # Get user resume, job description, and preferences from the database
        conn = sqlite3.connect("app.db")
        c = conn.cursor()
        c.execute("SELECT job_description, name, skills FROM resumes WHERE user_id = ? ORDER BY id DESC LIMIT 1", (message.user_id,))
        resume_result = c.fetchone()
        
        # Get interview type preference
        c.execute("SELECT interview_type FROM user_preferences WHERE user_id = ?", (message.user_id,))
        interview_type_result = c.fetchone()
        interview_type = interview_type_result[0] if interview_type_result else "technical"
        
        # Add debug logging to see what's happening with the interview type
        print(f"Raw interview type from DB: {interview_type_result}")
        print(f"Processed interview type: {interview_type}")
        
        # Ensure interview type is lowercase for consistent comparison
        interview_type = interview_type.lower() if interview_type else "technical"
        print(f"Normalized interview type: {interview_type}")
        
        # Force behavioral interview type for testing if needed
        # interview_type = "behavioral"
        # print(f"Forced interview type to: {interview_type}")

        conn.close()
        
        if resume_result:
            job_desc, name, user_skills = resume_result
            
            # Extract key skills and job requirements
            candidate_skills = extract_key_skills(user_skills)
            job_requirements = extract_job_requirements(job_desc)
            
            print(f"Candidate skills: {candidate_skills}")
            print(f"Job requirements: {job_requirements}")
            print(f"Interview type: {interview_type}")
            print(f"Current session state: {session_state}")
            
            # Evaluate the answer quality and determine appropriate feedback
            context = {
                'topic': session_state.current_topic,
                'concept': session_state.current_concept
            }
            
            # Check for short/vague answers
            is_short, is_vague, follow_up_question, quality_feedback = evaluate_answer_quality(message.message, context)
            
            # Technical terms detection (used for regular feedback)
            has_technical_terms = any(term in message.message.lower() for term in 
                                    ["algorithm", "function", "database", "code", "python", "sql", 
                                     "dataframe", "query", "model", "api", "class", "method"])
            
            # Determine feedback based on answer quality
            if (is_short or is_vague) and follow_up_question:
                # For short/vague answers, use the quality feedback and ask a follow-up
                feedback = quality_feedback
                
                # If we're not at the introduction stage, use the follow-up question 
                # instead of moving to the next topic/concept
                if session_state.last_question_type != "introduction" and follow_up_question:
                    # Return immediate follow-up question without changing state
                    response = f"{feedback} {follow_up_question}"
                    
                    # Save the response and return
                    conversation_history.append({"question": response, "answer": ""})
                    save_conversation(conversation_history)
                    return {"response": response}
            else:
                # For good answers, use regular feedback
                feedback = generate_answer_feedback(
                    answer_length=len(message.message),
                    contains_technical_terms=has_technical_terms
                )
            
            # Continue with the interview flow...
            
            # Case 1: First topic introduction
            if session_state.last_question_type == "introduction":
                # Generate personalized acknowledgment of their introduction
                intro_acknowledgment = generate_introduction_acknowledgment(message.message)
                
                # Determine the next topic to explore
                next_topic = determine_next_topic(
                    candidate_skills,
                    job_requirements,
                    session_state.explored_topics
                )
                
                # Generate a natural transition to the new topic
                topic_transition = generate_topic_transition(next_topic, is_first_topic=True)
                
                # Get concepts for this topic
                topic_concepts = extract_topic_concepts(next_topic, job_desc, user_skills)
                
                # Update session state
                session_state.current_topic = next_topic
                session_state.explored_topics.append(next_topic)
                session_state.current_concept = None  # Will start with experience question
                session_state.questions_in_current_topic = 1
                session_state.last_question_type = "topic_intro"
                session_state.concepts_covered[next_topic] = []
                
                # First ask about their experience with this topic - include intro acknowledgment
                response = f"{intro_acknowledgment} {topic_transition} Could you tell me about your experience with this area?"
            
            # Case 2: After topic introduction, start asking about concepts
            elif session_state.last_question_type == "topic_intro":
                # Get concepts for current topic if not already in session
                current_topic = session_state.current_topic
                
                if current_topic not in session_state.concepts_covered:
                    session_state.concepts_covered[current_topic] = []
                
                # Get concepts for this topic
                topic_concepts = extract_topic_concepts(current_topic, job_desc, user_skills)
                
                # Pick the first concept that hasn't been covered
                available_concepts = [c for c in topic_concepts if c not in session_state.concepts_covered[current_topic]]
                
                if available_concepts:
                    next_concept = available_concepts[0]
                    session_state.current_concept = next_concept
                    session_state.current_difficulty = "easy"
                    session_state.question_count_in_concept = 1
                    
                    # Get a concept-specific question at easy difficulty
                    concept_questions = get_concept_questions(
                        current_topic, 
                        next_concept, 
                        "easy", 
                        job_desc, 
                        interview_type,
                        user_skills
                    )
                    
                    print(f"Retrieved {len(concept_questions) if concept_questions else 0} concept questions for {next_concept} in {current_topic} with interview_type {interview_type}")
                    
                    if concept_questions:
                        # Introduce the concept and ask the first question
                        concept_intro = f"{feedback} Now, let's discuss {next_concept} in this area. "
                        response = f"{concept_intro}{concept_questions[0]}"
                    else:
                        # Fallback if no concept questions found
                        response = f"{feedback} Let's talk about {next_concept}. Can you explain the key principles or approaches in this area?"
                    
                    session_state.last_question_type = "concept_question"
                else:
                    # If all concepts covered, move to a new topic
                    # Determine the next topic to explore
                    next_topic = determine_next_topic(
                        candidate_skills,
                        job_requirements,
                        session_state.explored_topics
                    )
                    
                    # Generate a natural transition to the new topic
                    topic_transition = generate_topic_transition(next_topic, is_first_topic=False)
                    
                    # Update session state
                    session_state.current_topic = next_topic
                    session_state.explored_topics.append(next_topic)
                    session_state.current_concept = None
                    session_state.questions_in_current_topic = 1
                    session_state.last_question_type = "topic_intro"
                    session_state.concepts_covered[next_topic] = []
                    
                    # First ask about their experience with this topic
                    response = f"{feedback} {topic_transition} Could you tell me about your experience with this area?"
            
            # Case 3: Continue with concept questions or move to next concept/topic
            elif session_state.last_question_type == "concept_question":
                current_topic = session_state.current_topic
                current_concept = session_state.current_concept
                current_difficulty = session_state.current_difficulty
                question_count = session_state.question_count_in_concept
                
                # Determine if we should increase difficulty, move to next concept, or next topic
                if question_count < 2:
                    # Stay on same concept but increase difficulty if not already hard
                    next_difficulty = current_difficulty
                    if current_difficulty == "easy":
                        next_difficulty = "medium"
                    elif current_difficulty == "medium":
                        next_difficulty = "hard"
                    
                    # Update session state
                    session_state.current_difficulty = next_difficulty
                    session_state.question_count_in_concept += 1
                    
                    # Get a question at the new difficulty level
                    concept_questions = get_concept_questions(
                        current_topic, 
                        current_concept, 
                        next_difficulty, 
                        job_desc, 
                        interview_type,
                        user_skills
                    )
                    
                    if concept_questions:
                        response = f"{feedback} {concept_questions[0]}"
                    else:
                        # Fallback
                        response = f"{feedback} Going a bit deeper on {current_concept}, how would you approach a complex problem in this area?"
                    
                    session_state.last_question_type = "concept_question"
                else:
                    # We've asked enough about this concept, mark it as covered
                    if current_topic not in session_state.concepts_covered:
                        session_state.concepts_covered[current_topic] = []
                    
                    if current_concept not in session_state.concepts_covered[current_topic]:
                        session_state.concepts_covered[current_topic].append(current_concept)
                    
                    # Check if we should move to a new concept or new topic
                    if session_state.questions_in_current_topic < 5:
                        # Move to a new concept in same topic
                        topic_concepts = extract_topic_concepts(current_topic, job_desc, user_skills)
                        available_concepts = [c for c in topic_concepts if c not in session_state.concepts_covered[current_topic]]
                        
                        if available_concepts:
                            next_concept = available_concepts[0]
                            session_state.current_concept = next_concept
                            session_state.current_difficulty = "easy"
                            session_state.question_count_in_concept = 1
                            session_state.questions_in_current_topic += 1
                            
                            # Get a concept-specific question at easy difficulty
                            concept_questions = get_concept_questions(
                                current_topic, 
                                next_concept, 
                                "easy", 
                                job_desc, 
                                interview_type,
                                user_skills
                            )
                            
                            print(f"Retrieved {len(concept_questions) if concept_questions else 0} concept questions for {next_concept} in {current_topic} with interview_type {interview_type}")
                            
                            if concept_questions:
                                # Introduce the new concept and ask the first question
                                concept_intro = f"{feedback} Now, let's move on to {next_concept}. "
                                response = f"{concept_intro}{concept_questions[0]}"
                            else:
                                # Fallback
                                response = f"{feedback} Let's switch to discussing {next_concept}. Can you explain your approach to this area?"
                            
                            session_state.last_question_type = "concept_question"
                        else:
                            # No more concepts, move to a new topic
                            next_topic = determine_next_topic(
                                candidate_skills,
                                job_requirements,
                                session_state.explored_topics
                            )
                            
                            # Generate a natural transition to the new topic
                            topic_transition = generate_topic_transition(next_topic, is_first_topic=False)
                            
                            # Update session state
                            session_state.current_topic = next_topic
                            session_state.explored_topics.append(next_topic)
                            session_state.current_concept = None
                            session_state.questions_in_current_topic = 1
                            session_state.last_question_type = "topic_intro"
                            session_state.concepts_covered[next_topic] = []
                            
                            # First ask about their experience with this topic
                            response = f"{feedback} {topic_transition} Could you tell me about your experience with this area?"
                    else:
                        # We've asked enough about this topic, move to a new one
                        next_topic = determine_next_topic(
                            candidate_skills,
                            job_requirements,
                            session_state.explored_topics
                        )
                        
                        # Generate a natural transition to the new topic
                        topic_transition = generate_topic_transition(next_topic, is_first_topic=False)
                        
                        # Update session state
                        session_state.current_topic = next_topic
                        session_state.explored_topics.append(next_topic)
                        session_state.current_concept = None
                        session_state.questions_in_current_topic = 1
                        session_state.last_question_type = "topic_intro"
                        session_state.concepts_covered[next_topic] = []
                        
                        # First ask about their experience with this topic
                        response = f"{feedback} {topic_transition} Could you tell me about your experience with this area?"
            
            # Fallback case - topic follow-up or any other state
            else:
                # Determine the next topic to explore
                next_topic = determine_next_topic(
                    candidate_skills,
                    job_requirements,
                    session_state.explored_topics
                )
                
                # Generate a natural transition to the new topic
                topic_transition = generate_topic_transition(next_topic, is_first_topic=len(session_state.explored_topics)==0)
                
                # Update session state
                session_state.current_topic = next_topic
                session_state.explored_topics.append(next_topic)
                session_state.current_concept = None
                session_state.questions_in_current_topic = 1
                session_state.last_question_type = "topic_intro"
                session_state.concepts_covered[next_topic] = []
                
                # First ask about their experience with this topic
                response = f"{feedback} {topic_transition} Could you tell me about your experience with this area?"
            
            # Save updated session state
            save_session_state(message.user_id, session_state)
            
        else:
            # Fallback if no resume data found
            print("No resume data found for user. Using generic questions.")
            mock_responses = [
                "That's interesting! Can you tell me about a challenging project you worked on and how you overcame obstacles?",
                "Great answer. How do you typically approach problem-solving when given a new task?",
                "I see. Could you explain more about your technical expertise?",
                "Interesting perspective. What tools and technologies are you most comfortable with?",
                "That makes sense. How do you ensure the quality of your work?",
                "Thank you for sharing that. What are your career goals for the next few years?",
                "I appreciate your answer. How do you stay updated with the latest trends in your field?",
                "Very informative. Now, could you walk me through your approach when faced with ambiguous requirements?"
            ]
            response = mock_responses[min(len(conversation_history) % len(mock_responses), len(mock_responses) - 1)]
        
        # Save the response
        conversation_history.append({"question": response, "answer": ""})
        save_conversation(conversation_history)
        
        return {"response": response}
    except Exception as e:
        # Log the error for debugging
        print(f"Chat error: {str(e)}")
        traceback.print_exc()
        # Return a default response instead of raising an exception
        return {"response": "I understand. Let's move on to another question. Could you tell me about your expertise and what areas you're most interested in developing further?"}

@app.post("/api/generate-report")
async def api_generate_report(user_id: dict = Body(...)):
    try:
        # Extract user ID from request body
        user_id_value = user_id.get('user_id')
        if not user_id_value:
            raise HTTPException(status_code=400, detail="Missing user_id parameter")
        
        # Get resume and job description data from database
        conn = sqlite3.connect("app.db")
        c = conn.cursor()
        c.execute("SELECT job_description, skills FROM resumes WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id_value,))
        result = c.fetchone()
        conn.close()
        
        job_description = ""
        user_skills = ""
        if result:
            job_description, user_skills = result
        
        # Load conversation history
        conversation_history = load_conversation()
        if not conversation_history:
            raise HTTPException(status_code=400, detail="No conversation found")
        
        # Extract user answers and interview questions
        user_answers = []
        interview_questions = []
        for item in conversation_history:
            if "question" in item and item["question"]:
                interview_questions.append(item["question"])
            if "answer" in item and item["answer"]:
                user_answers.append({
                    "question": item["question"],
                    "answer": item["answer"]
                })
        
        # Count the number of exchanges for dynamic scoring
        num_exchanges = len(user_answers)
        
        # Check if this was an abbreviated interview (only introduction or very few exchanges)
        is_abbreviated_interview = num_exchanges <= 2
        
        # If abbreviated interview, provide special feedback
        if is_abbreviated_interview:
            print(f"Abbreviated interview detected with only {num_exchanges} exchanges")
            
            # Create a special report for abbreviated interviews
            return {
                "success": True,
                "abbreviated_interview": True,
                "metrics": {
                    "f1Score": 0.0,
                    "rougeScore": 0.0,
                    "bleuScore": 0.0,
                    "questionAnswers": [
                        {
                            "question": qa["question"],
                            "userAnswer": qa["answer"],
                            "idealAnswer": "A detailed response that addresses the key points with specific examples.",
                            "score": 0.0 
                        } for qa in user_answers
                    ]
                },
                "report": {
                    "overall_score": None,  # No score for abbreviated interviews
                    "technical_score": None,
                    "communication_score": None,
                    "engagement_score": None,
                    "strengths": ["The interview was ended before a complete assessment could be made."],
                    "improvements": ["Complete a full interview to receive detailed feedback on your performance."],
                    "examples": {
                        "strong": [],
                        "needsImprovement": []
                    },
                    "resources": [
                        {
                            "title": "Interview Preparation Guide",
                            "description": "A comprehensive guide to help you prepare for technical and behavioral interviews.",
                            "link": "https://www.themuse.com/advice/interview-preparation-guide"
                        },
                        {
                            "title": "Practice Technical Interviews",
                            "description": "Resources to practice technical interviews with real-world scenarios.",
                            "link": "https://leetcode.com/"
                        }
                    ],
                    "message": "This interview was ended early after your introduction. To receive meaningful feedback, try completing a full interview with technical and behavioral questions."
                }
            }
        
        # For normal interviews, continue with the original logic
        # Calculate dynamic scores based on conversation length and content
        # More exchanges generally suggest better engagement
        engagement_score = min(85, 50 + (num_exchanges * 5))
        
        # Check answer lengths for communication score
        avg_answer_length = 0
        if num_exchanges > 0:
            total_length = sum(len(answer["answer"]) for answer in user_answers)
            avg_answer_length = total_length / num_exchanges
        
        # Longer answers typically indicate better communication (up to a point)
        communication_score = min(90, 40 + min(50, avg_answer_length / 5))
        
        # Calculate technical score based on keyword matches
        technical_keywords = [
            "python", "sql", "database", "analysis", "modeling", "etl", "pipeline", 
            "hadoop", "spark", "aws", "cloud", "machine learning", "statistics", 
            "algorithm", "data engineering", "data science", "visualization",
            "tableau", "power bi", "bi", "excel", "analytics"
        ]
        
        # Extract keywords from the job description
        job_keywords = []
        if job_description:
            # Convert to lowercase for matching
            job_desc_lower = job_description.lower()
            for keyword in technical_keywords:
                if keyword in job_desc_lower:
                    job_keywords.append(keyword)
        
        # Count technical keywords in answers
        keyword_count = 0
        for answer in user_answers:
            answer_lower = answer["answer"].lower()
            for keyword in technical_keywords:
                if keyword in answer_lower:
                    keyword_count += 1
        
        # Calculate technical score based on keyword density
        technical_score = min(90, 50 + (keyword_count * 3))
        
        # Overall score is weighted average of the three scores
        overall_score = int((technical_score * 0.4) + (communication_score * 0.3) + (engagement_score * 0.3))
        
        # Generate personalized strengths based on answers
        strengths = []
        
        # Check for detailed technical explanations
        if technical_score > 70:
            strengths.append("Demonstrated strong technical knowledge with detailed explanations")
        
        # Check for comprehensive answers
        if avg_answer_length > 100:
            strengths.append("Provided thorough and comprehensive responses to questions")
        
        # Check for consistent engagement
        if num_exchanges >= 4:
            strengths.append("Maintained consistent engagement throughout the interview")
        
        # Check for alignment with job description
        job_keyword_matches = 0
        for answer in user_answers:
            answer_lower = answer["answer"].lower()
            for keyword in job_keywords:
                if keyword in answer_lower:
                    job_keyword_matches += 1
        
        if job_keyword_matches > 3:
            strengths.append("Effectively aligned responses with job requirements")
        
        # Ensure minimum strengths
        if len(strengths) < 2:
            strengths.append("Willingness to engage with the interview process")
            if technical_score > 60:
                strengths.append("Demonstrated basic technical knowledge relevant to the position")
            else:
                strengths.append("Showed interest in the field and position")
        
        # Generate areas for improvement
        improvements = []
        
        # Technical knowledge improvements
        if technical_score < 70:
            improvements.append("Enhance technical explanations with more specific examples and terminology")
        
        # Answer length improvements
        if avg_answer_length < 70:
            improvements.append("Provide more detailed responses to showcase your experience and knowledge")
        
        # Job alignment improvements
        if job_keyword_matches < 3 and job_keywords:
            improvements.append("Focus more on addressing the specific requirements mentioned in the job description")
        
        # Ensure minimum improvements
        if len(improvements) < 2:
            improvements.append("Continue practicing interview responses to build confidence")
            improvements.append("Consider providing more concrete examples from your experience")
        
        # Find strongest and weakest answers for examples
        strongest_answers = []
        needs_improvement_answers = []
        
        # Sort answers by length (as a simple heuristic for answer quality)
        sorted_answers = sorted(user_answers, key=lambda x: len(x["answer"]), reverse=True)
        
        # Get strongest answers (up to 2)
        if len(sorted_answers) >= 2:
            strongest_answers = [
                {
                    "question": sorted_answers[0]["question"],
                    "answer": sorted_answers[0]["answer"],
                    "reason": "Provided a comprehensive response that demonstrates clear understanding."
                },
                {
                    "question": sorted_answers[1]["question"],
                    "answer": sorted_answers[1]["answer"],
                    "reason": "Showed good communication skills and technical knowledge."
                }
            ]
        elif len(sorted_answers) == 1:
            strongest_answers = [
                {
                    "question": sorted_answers[0]["question"],
                    "answer": sorted_answers[0]["answer"],
                    "reason": "Provided a good response that shows your understanding."
                }
            ]
        
        # Get answers needing improvement (using shorter answers as proxy)
        if len(sorted_answers) >= 4:
            needs_improvement_answers = [
                {
                    "question": sorted_answers[-1]["question"],
                    "answer": sorted_answers[-1]["answer"],
                    "betterApproach": "Consider expanding your answer with specific examples and more technical details."
                },
                {
                    "question": sorted_answers[-2]["question"],
                    "answer": sorted_answers[-2]["answer"],
                    "betterApproach": "Try to provide more context and explain the concepts in greater depth."
                }
            ]
        elif len(sorted_answers) >= 2:
            needs_improvement_answers = [
                {
                    "question": sorted_answers[-1]["question"],
                    "answer": sorted_answers[-1]["answer"],
                    "betterApproach": "Expand your answer with more details and concrete examples from your experience."
                }
            ]
        
        # Generate targeted resources based on the conversation
        resources = []
        
        # Check for technical topics to recommend resources
        if "sql" in user_skills.lower() or any("sql" in a["answer"].lower() for a in user_answers):
            resources.append({
                "title": "Advanced SQL Techniques",
                "description": "Enhance your SQL skills with advanced querying and optimization techniques.",
                "link": "https://mode.com/sql-tutorial/advanced-sql-techniques/"
            })
        
        if "python" in user_skills.lower() or any("python" in a["answer"].lower() for a in user_answers):
            resources.append({
                "title": "Python for Data Engineering",
                "description": "Master Python libraries and techniques for efficient data processing and ETL workflows.",
                "link": "https://realpython.com/python-data-cleaning-numpy-pandas/"
            })
        
        if "etl" in user_skills.lower() or "pipeline" in user_skills.lower() or any("etl" in a["answer"].lower() for a in user_answers):
            resources.append({
                "title": "Modern Data Engineering Pipelines",
                "description": "Best practices for building scalable, maintainable ETL pipelines.",
                "link": "https://www.startdataengineering.com/"
            })
        
        if "aws" in user_skills.lower() or "cloud" in user_skills.lower() or any("aws" in a["answer"].lower() for a in user_answers):
            resources.append({
                "title": "AWS for Data Engineering",
                "description": "Learn to leverage AWS services for efficient data processing and analytics.",
                "link": "https://aws.amazon.com/big-data/what-is-a-data-lake/"
            })
        
        # Ensure we have at least some resources
        if len(resources) < 2:
            resources.append({
                "title": "Technical Interview Preparation",
                "description": "Practical tips and strategies for excelling in technical interviews.",
                "link": "https://www.educative.io/courses/grokking-the-system-design-interview"
            })
            resources.append({
                "title": "Data Engineering Fundamentals",
                "description": "Master the core concepts and tools of modern data engineering.",
                "link": "https://www.dataquest.io/path/data-engineer/"
            })
        
        # Create metrics object
        metrics = {
            "f1Score": technical_score / 100,
            "rougeScore": communication_score / 100,
            "bleuScore": engagement_score / 100,
            "questionAnswers": [
                {
                    "question": qa["question"],
                    "userAnswer": qa["answer"],
                    "idealAnswer": "A detailed response that addresses the key points with specific examples.",
                    "score": min(1.0, 0.5 + (len(qa["answer"]) / 500))  # Score based on answer length
                } for qa in user_answers
            ]
        }
        
        return {
            "success": True,
            "abbreviated_interview": False,
            "metrics": metrics,
            "report": {
                "overall_score": overall_score,
                "technical_score": technical_score,
                "communication_score": communication_score,
                "engagement_score": engagement_score,
                "strengths": strengths,
                "improvements": improvements,
                "examples": {
                    "strong": strongest_answers,
                    "needsImprovement": needs_improvement_answers
                },
                "resources": resources
            }
        }
    except Exception as e:
        print(f"Report generation error: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 