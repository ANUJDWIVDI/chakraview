import streamlit as st
import google.generativeai as genai
from bs4 import BeautifulSoup
import requests
import os
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import pandas as pd
import PyPDF2
from io import BytesIO
import matplotlib.pyplot as plt
from datetime import datetime

# --- Initialization ---
nltk.download('punkt')
nltk.download('stopwords')

# --- Configuration ---
GENAI_KEY = os.getenv("GENAI_KEY", "AIzaSyDK-Fwq6bvT7iIN8RvDjRkn7idsfRpzu3w")
MODEL_NAME = "gemini-2.0-flash"

# Load default DSU knowledge
try:
    with open("dsu.txt", "r", encoding='utf-8') as f:
        DEFAULT_KNOWLEDGE = f.read()
except FileNotFoundError:
    DEFAULT_KNOWLEDGE = ""
    st.warning("dsu.txt not found - some functionality may be limited")

# Initialize AI model
try:
    genai.configure(api_key=GENAI_KEY)
    llm = genai.GenerativeModel(MODEL_NAME)
except Exception as e:
    st.error(f"Model initialization error: {str(e)}")
    st.stop()

# --- Document Processing ---
def extract_text(file):
    """Extract text from uploaded files (PDF or text)"""
    if file.type == "application/pdf":
        try:
            pdf_reader = PyPDF2.PdfReader(BytesIO(file.read()))
            return "\n".join([page.extract_text() for page in pdf_reader.pages])
        except Exception as e:
            st.error(f"PDF processing error: {str(e)}")
            return ""
    elif file.type == "text/plain":
        return file.read().decode("utf-8")
    return ""

def chunk_text(text, chunk_size=500):
    """Split text into semantic chunks for processing"""
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < chunk_size:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

# --- Enhanced Web Scraping Engine ---
def scrape_dsu_website(url, scrape_params):
    """Scrape different sections of DSU website"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        results = {}
        
        # Scrape different parameters
        for param in scrape_params:
            if param == 'news':
                results['news'] = [item.get_text(strip=True) for item in soup.select('.news-title')[:5]]
            elif param == 'events':
                results['events'] = [item.get_text(strip=True) for item in soup.select('.event-title')[:5]]
            elif param == 'courses':
                results['courses'] = [item.get_text(strip=True) for item in soup.select('.course-name')[:5]]
            elif param == 'faculty':
                results['faculty'] = [item.get_text(strip=True) for item in soup.select('.faculty-name')[:3]]
        
        return "\n\n".join([f"{k}:\n" + "\n".join(v) for k, v in results.items()])
    except Exception as e:
        st.error(f"Scraping error: {str(e)}")
        return ""

# --- Knowledge Management System ---
class DSURAGSystem:
    def __init__(self):
        self.llm = llm
        self.knowledge_base = DEFAULT_KNOWLEDGE
        self.system_prompt = """
        You are DSU Knowledge Nexus, the official AI assistant for Dayananda Sagar University.
        You have access to the university's knowledge base including:
        - Academic programs and admissions
        - Faculty information
        - Events and announcements
        - Research opportunities
        
        Response Guidelines:
        1. Be specific with names, dates, and numbers when available
        2. For admissions: mention deadlines and requirements
        3. For faculty: include departments and positions
        4. For events: include dates and locations
        5. Maintain professional academic tone
        6. If unsure, guide to official contacts/website
        """
    
    def update_knowledge(self, new_content):
        """Update the knowledge base with new content"""
        self.knowledge_base += "\n\n" + new_content
    
    def generate_response(self, prompt):
        """Generate response using RAG with local knowledge"""
        try:
            response = self.llm.generate_content(
                f"{self.system_prompt}\n\n"
                f"Knowledge Base:\n{self.knowledge_base}\n\n"
                f"Question: {prompt}\n\n"
                "Provide accurate information based on the knowledge above."
            )
            return response.text
        except Exception as e:
            return f"System error: {str(e)}"

# --- Visualization Functions ---
def plot_program_popularity():
    """Top programs by applications"""
    data = {
        "Program": ["CSE (AI/ML)", "Data Science", "Electronics", "Mechanical"],
        "Applications": [450, 380, 320, 280]
    }
    df = pd.DataFrame(data)
    
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(df["Program"], df["Applications"], color=['#4C72B0', '#55A868', '#C44E52', '#8172B2'])
    ax.set_title("Most Popular Programs (2024)")
    ax.set_ylabel("Applications")
    plt.xticks(rotation=45)
    st.pyplot(fig)

def plot_faculty_distribution():
    """Faculty by department"""
    data = {
        "Department": ["CSE", "ECE", "Mechanical", "Sciences", "Management"],
        "Faculty Count": [32, 28, 24, 18, 22]
    }
    df = pd.DataFrame(data)
    
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.pie(df["Faculty Count"], labels=df["Department"], autopct='%1.1f%%',
           colors=['#FF9999','#66B2FF','#99FF99','#FFCC99','#FFD700'])
    ax.set_title('Faculty Distribution by Department')
    st.pyplot(fig)

def plot_event_timeline():
    """Upcoming events timeline"""
    events = {
        "NCISABR 2025": "2025-01-15",
        "DSU Pharmacon": "2024-11-20",
        "Hackathon": "2024-09-10",
        "Convocation": "2024-10-28"
    }
    dates = [datetime.strptime(d, "%Y-%m-%d") for d in events.values()]
    
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(dates, [1]*len(dates), 'o', markersize=10)
    ax.set_yticks([])
    ax.set_xticks(dates)
    ax.set_xticklabels(list(events.keys()))
    ax.set_title('Upcoming DSU Events')
    plt.xticks(rotation=45)
    st.pyplot(fig)

def plot_placement_stats():
    """Placement statistics"""
    years = [2021, 2022, 2023, 2024]
    placements = [85, 88, 91, 94]  # Percentage
    
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(years, placements, marker='o', linestyle='-', color='#4C72B0')
    ax.set_title("Placement Percentage (2021-2024)")
    ax.set_ylabel("Placement %")
    ax.set_xlabel("Year")
    ax.set_ylim(80, 100)
    st.pyplot(fig)

# --- Predefined Questions ---
PREPOPULATED_QUESTIONS = [
    "What are the admission requirements for B.Tech in AI/ML?",
    "List upcoming events with dates and contacts",
    "Who are the key faculty in Computer Science department?",
    "What scholarship options exist for research students?",
    "How does DSU rank for placements nationally?"
]

# --- Main Application ---
def main():
    st.set_page_config(
        page_title="DSU Knowledge Nexus",
        page_icon="🏛️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            width: 100%;
            margin-bottom: 5px;
        }
        .question-box {
            padding: 10px;
            margin: 5px 0;
            border-left: 3px solid #4CAF50;
            background-color: #f8f9fa;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize system
    rag_system = DSURAGSystem()
    
    # Sidebar - Data Collection
    with st.sidebar:
        st.header("📚 Knowledge Management")
        
        # Document Upload
        with st.expander("📄 Upload Documents", expanded=True):
            uploaded_file = st.file_uploader(
                "Upload DSU documents (PDF/TXT)",
                type=["pdf", "txt"],
                accept_multiple_files=False
            )
            if st.button("Process Document") and uploaded_file:
                with st.spinner("Processing..."):
                    text = extract_text(uploaded_file)
                    if text:
                        rag_system.update_knowledge(text)
                        st.success("Document added to knowledge base!")
        
        # Enhanced Web Scraping
        with st.expander("🌐 Scrape DSU Website", expanded=True):
            scrape_url = st.text_input("URL to scrape", "https://www.dsu.edu.in")
            scrape_params = st.multiselect(
                "Select content to scrape",
                ['news', 'events', 'courses', 'faculty'],
                default=['news', 'events']
            )
            
            if st.button("Scrape Selected Content"):
                with st.spinner("Scraping..."):
                    scraped_data = scrape_dsu_website(scrape_url, scrape_params)
                    if scraped_data:
                        rag_system.update_knowledge(scraped_data)
                        st.success("Scraped content added to knowledge base!")
        
        # Predefined Questions
        with st.expander("💡 Quick Questions", expanded=True):
            st.markdown("**Click to ask:**")
            for question in PREPOPULATED_QUESTIONS:
                if st.button(question, key=f"q_{PREPOPULATED_QUESTIONS.index(question)}"):
                    # Store question in session state
                    st.session_state.pending_question = question
        
        # Visualizations
        with st.expander("📊 DSU Insights", expanded=False):
            plot_program_popularity()
            plot_faculty_distribution()
            plot_event_timeline()
            plot_placement_stats()
    
    # Main Chat Interface
    st.title("🏛️ DSU Knowledge Nexus")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant", 
            "content": "Welcome to DSU Knowledge Nexus! How can I help you today?"
        }]
    
    # Display chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Handle predefined questions
    if hasattr(st.session_state, 'pending_question'):
        # Create a text input with the question pre-filled
        question_input = st.text_input(
            "Ask about DSU...",
            value=st.session_state.pending_question,
            key="question_input"
        )
        
        # If user presses enter or modifies the question
        if question_input:
            # Add to chat history
            st.session_state.messages.append({"role": "user", "content": question_input})
            
            # Generate response
            with st.spinner("Searching knowledge base..."):
                response = rag_system.generate_response(question_input)
            
            # Add assistant response
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Clear pending question
            del st.session_state.pending_question
            
            # Rerun to update UI
            st.rerun()
    else:
        # Normal chat input
        if prompt := st.chat_input("Ask about DSU..."):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Generate response
            with st.spinner("Analyzing DSU resources..."):
                response = rag_system.generate_response(prompt)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Rerun to update UI
            st.rerun()

if __name__ == "__main__":
    main()