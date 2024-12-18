from flask import Flask, render_template, redirect, session, url_for, request, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from neo4j import GraphDatabase
from werkzeug.security import generate_password_hash, check_password_hash
import os
from user_neo import process_uploaded_document_and_create_relationships, extract_text_from_document
from flask import Flask, render_template, jsonify
import requests
import pprint 
from neo_4j_user_handler import Neo4jHandler
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai # Assuming you have a Neo4jHandler class
import uuid
from neo_handler import Neo4jHandler1
from apscheduler.schedulers.background import BackgroundScheduler
import time

genai.configure(api_key="AIzaSyCv9KO5acAkV2_T1p9PKVNJSrmeswE8_AA")

# ---- App Initialization ----
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Replace with a strong secret key
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ---- Neo4j Credentials ----
URI = "neo4j+s://608b8766.databases.neo4j.io"
AUTH = ("neo4j", "AZE3H4xpn9vP-Uwwz_H5fhiGSFZivlSvKGImf1ZoNjM")


# Neo4j credentials
uri = "neo4j+s://608b8766.databases.neo4j.io"
username = "neo4j"
password = "AZE3H4xpn9vP-Uwwz_H5fhiGSFZivlSvKGImf1ZoNjM"

driver = GraphDatabase.driver(URI, auth=AUTH)


# Global chat history
chat_history = []

# ---- Scheduler to clear chat history every 30 minutes ----
def clear_chat_history():
    global chat_history
    chat_history = []  # Clear the chat history list
    print("Chat history cleared.")

# Setup the scheduler to run every 30 minutes
scheduler = BackgroundScheduler()
scheduler.add_job(func=clear_chat_history, trigger="interval", minutes=30)
scheduler.start()



# ---- Flask-Login Setup ----
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# ---- User Model ----
class User(UserMixin):
    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    with driver.session() as session:
        result = session.read_transaction(get_user_by_id, user_id)
        if result:
            return User(id=result['id'], name=result['name'], email=result['email'])
    return None

def get_user_by_id(tx, user_id):
    query = "MATCH (u:User {id: $id}) RETURN u.id AS id, u.name AS name, u.email AS email"
    result = tx.run(query, id=user_id)
    return result.single()

# ---- Routes ----

@app.route("/")
def home():
    return render_template("intro.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Pass both email and password to the authenticate_user function
        with driver.session() as session:
            user = session.read_transaction(authenticate_user, email, password)
        
        # Handle user authentication result
        if user:
            # Successful login, proceed with session management
            login_user(User(id=user['id'], name=user['name'], email=user['email']))
            return redirect('/dashboard')
        else:
            # Handle failed login attempt
            flash('Invalid email or password.')
            return redirect('/login')
    return render_template('login.html')

@app.route('/upload_content')
def upload_content():
    return render_template('upload_content.html')  # Link this to your upload content page


@app.route('/upload', methods=['POST'])
def upload():
    # Check if a file or text is submitted
    file = request.files.get('file')
    additional_text = request.form.get('additional_text')

    # Process text or file content
    if file:
        # Save the file
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        # Extract content from the uploaded document (Assuming the file is a text file)
        document_content = extract_text_from_document(file_path)

        # Call function to process document and create Neo4j relationships
        process_uploaded_document_and_create_relationships(file_path)

    elif additional_text.strip():
        document_content = additional_text.strip()

        # Call Gemma API to generate Neo4j commands from the text (if needed)
        process_uploaded_document_and_create_relationships(document_content)

    else:
        return jsonify({"error": "No document or text provided"}), 400

    # Return a success response
    return jsonify({"message": "Document processed successfully and relationships created."}), 200



def authenticate_user(tx, email, password):
    query = """
    MATCH (u:User {email: $email})
    RETURN u.id AS id, u.name AS name, u.email AS email, u.password AS password
    """
    result = tx.run(query, email=email)
    user = result.single()
    if user and check_password_hash(user["password"], password):
        return user
    return None

# Helper functions to interact with Neo4j
def get_user_by_email(tx, email):
    query = "MATCH (u:User {email: $email}) RETURN u"
    result = tx.run(query, email=email)
    return result.single()

def create_user(tx, name, email, password, bio, occupation, interests, fcs_score=10):
    # Use email as id
    user_id = email  # Set the email as the user id
    
    query = """
    CREATE (u:User {id: $user_id, name: $name, email: $email, password: $password, bio: $bio, occupation: $occupation, fcs_score: $fcs_score})
    """
    tx.run(query, user_id=user_id, name=name, email=email, password=password, bio=bio, occupation=occupation, fcs_score=fcs_score)
    
    # If interests are provided, store them as relationships or properties
    if interests:
        for interest in interests:
            tx.run("""
            MATCH (u:User {email: $email})
            MERGE (i:Interest {name: $interest})
            MERGE (u)-[:INTERESTED_IN]->(i)
            """, email=email, interest=interest)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        # Get data from the form
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        bio = request.form.get("bio", "")
        occupation = request.form.get("occupation")
        interests = request.form.getlist("interests")  # This will capture multiple interests if selected

        # Hash the password
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        with driver.session() as session:
            # Check if user already exists
            existing_user = session.read_transaction(get_user_by_email, email)
            if existing_user:
                flash("User already exists. Please log in.", "danger")
                return redirect(url_for("login"))

            # Create new user in Neo4j, set default FCS score to 10
            session.write_transaction(create_user, name, email, hashed_password, bio, occupation, interests)
            flash("Signup successful! Please log in.", "success")
            return redirect(url_for("login"))
        
    return render_template("signup.html")


# ---- Dashboard ----
@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == "POST":
        traction = int(request.form.get("traction"))
        innovation = int(request.form.get("innovation"))
        engagement = int(request.form.get("engagement"))
        
        with driver.session() as session:
            session.write_transaction(save_metrics, current_user.id, traction, innovation, engagement)
            fcs_score = calculate_fcs(traction, innovation, engagement)
            session.write_transaction(save_fcs_score, current_user.id, fcs_score)
        
        flash("Metrics saved and FCS calculated successfully!", "success")
    
    with driver.session() as session:
        fcs = session.read_transaction(get_user_fcs, current_user.id)
    
    return render_template("dashboard.html", name=current_user.name, fcs=fcs, user_id=current_user.id)


def save_metrics(tx, user_id, traction, innovation, engagement):
    query = """
    MATCH (u:User {id: $user_id})
    MERGE (u)-[:HAS_METRIC]->(:Metric {type: 'Traction', score: $traction})
    MERGE (u)-[:HAS_METRIC]->(:Metric {type: 'Innovation', score: $innovation})
    MERGE (u)-[:HAS_METRIC]->(:Metric {type: 'Engagement', score: $engagement})
    """
    tx.run(query, user_id=user_id, traction=traction, innovation=innovation, engagement=engagement)

def calculate_fcs(traction, innovation, engagement):
    return round(traction * 0.4 + innovation * 0.3 + engagement * 0.3, 2)

def save_fcs_score(tx, user_id, fcs_score):
    query = """
    MATCH (u:User {id: $user_id})
    SET u.fcs_score = $fcs_score
    """
    tx.run(query, user_id=user_id, fcs_score=fcs_score)

def get_user_fcs(tx, user_id):
    query = "MATCH (u:User {id: $user_id}) RETURN u.fcs_score AS fcs_score"
    result = tx.run(query, user_id=user_id)
    record = result.single()
    return record["fcs_score"] if record else "Not calculated"


@app.route('/alliance-load' , methods=['GET', 'POST'])
def alliance_load():
    print("Alliance Load")
    return render_template('alliance_load.html')

@app.route('/events', methods=['GET', 'POST'])
def events():
    if request.method == 'POST':
        # Get the event search and city selection from the form
        event_search = request.form.get('event-search', '')
        city = request.form.get('city-select', '')
        name = request.form.get('name', '')

        # Default to "business events" if no event search is entered
        if not event_search:
            event_search = "business events/meetups"

        # Default to "global" if no city is selected
        if not city:
            city = "global"

    try:
        # Credentials
        username = 'anujd_XYDmo'
        password = 'Okankith_12345'

        print("------xxxxxxxxx---------")
        print(event_search)
        print(city)
        print("------xxxxxxxxx---------")

        # Payload for the API
        payload = {
            "source": "google_search",
            "query": event_search + " buisness / meetups / events ",
            "geo_location": city,
            "parse": True
        }

        # API Request
        response = requests.post(
            'https://realtime.oxylabs.io/v1/queries',
            auth=(username, password),
            json=payload
        )

        # Print the raw response for debugging
        print("Raw response status code:", response.status_code)
        pprint.pprint(response.json())

        # Parse the JSON response
        data = response.json()

        # Initialize an empty list to store event details
        results = []

        # Extract event details from the response
        if 'results' in data:
            for event in data['results'][0]['content']['results']['organic']:
                event_details = {
                    'title': event.get('title', 'No title available'),
                    'description': event.get('desc', 'No description available'),
                    'url': event.get('url', 'No URL available'),
                    'favicon': event.get('favicon_text', 'No favicon available')
                }
                results.append(event_details)

        # Return the results to the template
        return render_template('events.html', events=results, name=name)    

    except Exception as e:
        # Log exceptions for debugging
        print(f"Exception occurred: {e}")
        return render_template('events.html', events=[], error="Failed to load events.")


@app.route('/append-knowledge', methods=['POST'])
def append_knowledge():


    # Get the list of selected events from the form
    selected_events = request.form.getlist('selected_events')
    user_id = request.form.get('user_id')

    # Print the selected events to the console for debugging
    print("Selected Events:", selected_events)
    print("User ID:", user_id)

    # Use the Neo4jHandler to update the user's interests
    try:
        uri = "neo4j+s://608b8766.databases.neo4j.io"
        username = "neo4j"
        password = "AZE3H4xpn9vP-Uwwz_H5fhiGSFZivlSvKGImf1ZoNjM"

        neo4j_handler = Neo4jHandler(uri, username, password)
        neo4j_handler.update_user_interests(user_id=user_id, events=selected_events)
    except Exception as e:
        print("Error updating interests:", e)

     # Close the Neo4j session and driver after usage
    neo4j_handler.close()

    return redirect(url_for('dashboard')) 


@app.route('/search-users', methods=['GET'])
def search_users():
    query = request.args.get('query', '')  # Get the query or default to an empty string
    print("Query:", query)

    # Neo4j handler
    neo4j_handler = Neo4jHandler(uri, username, password)
    
    if query:
        # If there's a query, use it to search
        users = neo4j_handler.search_users(query)
        print("Users:", users)
    else:
        # If no query is provided, fetch all users
        users = neo4j_handler.search_users('')
        print("All Users:", users)

    # Ensure the response contains all required fields for each user
    response = {
        "users": [
            {
                "name": user.get("name", "N/A"),
                "bio": user.get("bio", "N/A"),
                "interests": user.get("interests", "N/A"),
                "occupation": user.get("occupation", "N/A")
            }
            for user in users
        ]
    }

    neo4j_handler.close()
    
    return jsonify(response)


# ---- Logout ----
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "success")
    return redirect(url_for("login"))


@app.route('/chat', methods=['POST'])
def chat():
    global chat_history
    # Fetching user_id and message from JSON request
    data = request.get_json()
    user_id = data.get('user_id')
    print("User ID:", user_id)
    message = data.get('message')
    print("Message:", message)

    # Neo4j credentials
    uri = "neo4j+s://608b8766.databases.neo4j.io"
    username = "neo4j"
    password = "AZE3H4xpn9vP-Uwwz_H5fhiGSFZivlSvKGImf1ZoNjM"

    # Fetch user details from Neo4j
    neo4j_handler = Neo4jHandler1(uri, username, password)
    user_details = neo4j_handler.get_user_details(user_id)
    print("User Details:", user_details)

    # Safely access the bio and occupation fields, provide default values if they don't exist
    bio = user_details.get('bio', 'No bio available')
    print("Bio:", bio)
    occupation = user_details.get('occupation', 'Unknown occupation')
    print("Occupation:", occupation)
    username1 = user_details.get('name', 'Unknown user')
    print("Username:", username1)
    # Check if chat history exists
    
    print("Chat History from usrerrrrr :", chat_history)
    print(username1)
    if not chat_history:  # If no chat history, generate a welcome message
        prompt = f"You have to chat with {username1} , address him with his name and tell - what a wonderful day to have conversation - next go on to have more info about him - this si some breif of me {bio} , and this is my occupation : {occupation}, now chat with me giv eme a warm wecom and see what could i love to talk about , very freindly while also proffessional , reassure. ur here to help ,do not inclidu any formatting , no * or anything only plain text "
    else:  # If chat history exists, continue the chat
        prompt = f"chat history: {chat_history}. Continue based on that.keep essense alive"

    # Generate the response using Google Generative AI
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)

    # Save the chat history, including the current message and response
    chat_history.append(response.text)

    return jsonify({
        "chat_history": chat_history,
        "response": response.text
    })

# Helper function to save chat history
def save_chat_history(user_id, message, response_text):
    # Generate unique ID for the chat
    chat_id = str(uuid.uuid4())

    # Save the chat history
    chat_history = {
        "chat_id": chat_id,
        "user_id": user_id,
        "messages": [
            {"message": message, "role": "user"},
            {"message": response_text, "role": "bot"}
        ]
    }

    # In this example, we're just printing it; you can save it to your database
    print("Chat History Saved:", chat_history)

    return chat_history

# Helper function to get chat history (you can fetch from the database)
def get_chat_history(user_id):
    # For simplicity, returning an empty list here, but you would fetch it from the database
    return []  # or fetch from your database

@app.route('/NitiSense', methods=['GET'])
def NitiSense():
    print("NitiSense calling")
    print(current_user.id)
    return render_template('NitiSense.html',user_id=current_user.id)

if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
