import os
import json
import requests
from flask import Flask, request, redirect, render_template
from werkzeug.utils import secure_filename
from neo4j import GraphDatabase
from PyPDF2 import PdfReader
from neo4j import GraphDatabase

# ---- App Initialization ----
app = Flask(__name__)
app.secret_key = 'supersecretkey'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ---- Neo4j Credentials ----
URI = "neo4j+s://608b8766.databases.neo4j.io"
AUTH = ("neo4j", "AZE3H4xpn9vP-Uwwz_H5fhiGSFZivlSvKGImf1ZoNjM")
driver = GraphDatabase.driver(URI, auth=AUTH)

# ---- Gemini API Key ----
API_KEY = "AIzaSyBxTDsVQQoHkjOq4Qny5-7sOlvyna2f0E8"

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_pdf(file_path):
    text = ''
    reader = PdfReader(file_path)
    for page in reader.pages:
        text += page.extract_text()
    return text

def process_text(file_path):
    with open(file_path, 'r') as file:
        return file.read()



def summarize_content(content):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=" + API_KEY
    payload = json.dumps({
        "contents": [
            {
                "parts": [
                    {
                        "text": "Please summarize the following document while preserving its original essence. Make the summary as concise as possible, highlighting the main points. The document can be technical, so make sure to retain key terms and concepts. If the document contains sections, make sure to summarize each section clearly."
                    },
                    {
                        "text": content
                    }
                ]
            }
        ]
    })
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=payload, headers=headers)

    # Parse the response
    summary = response.json()

    # Extract the summary text from the response
    summarized_text = summary['candidates'][0]['content']['parts'][0]['text']
    
    return summarized_text



def save_to_neo4j(content, summarized_text):
    # Assuming 'driver' is your Neo4j connection driver
    session = driver.session()
    
    try:
        # Create a transaction using the session
        with session.begin_transaction() as tx:
            # Write the content and summarized text to Neo4j
            tx.run("""
                CREATE (n:Document {content: $content, summary: $summary})
            """, content=content, summary=summarized_text)
        
        # Transaction is committed automatically when exiting the 'with' block
    
    except Exception as e:
        print(f"Error saving to Neo4j: {e}")
    finally:
        session.close()

# ---- Flask Routes ----
@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        # Handle uploaded file
        file = request.files.get('file')
        additional_text = request.form.get('additional_text')

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Process file (PDF or Text)
            if filename.endswith('.pdf'):
                content = process_pdf(file_path)
            elif filename.endswith('.txt'):
                content = process_text(file_path)

            # Add additional text content to the file content
            if additional_text:
                content += '\n' + additional_text

            # Summarize content using Gemini
            summarized_text = summarize_content(content)

            # Save original and summarized content to Neo4j
            save_to_neo4j(content, summarized_text)

            return f"File uploaded and processed successfully! Check Neo4j for updated content."

    return render_template("upload_content.html")

if __name__ == "__main__":
    app.run(debug=True)
