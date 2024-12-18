from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from neo4j import GraphDatabase
from werkzeug.security import generate_password_hash, check_password_hash
import os
from user_neo import process_uploaded_document_and_create_relationships, extract_text_from_document
from flask import Flask, render_template, jsonify
import requests
import pprint 

# ---- App Initialization ----
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Replace with a strong secret key
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ---- Neo4j Credentials ----
URI = "neo4j+s://608b8766.databases.neo4j.io"
AUTH = ("neo4j", "AZE3H4xpn9vP-Uwwz_H5fhiGSFZivlSvKGImf1ZoNjM")

driver = GraphDatabase.driver(URI, auth=AUTH)

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
    return redirect(url_for("login"))

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

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        # When signing up, use 'pbkdf2:sha256' for password hashing
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        with driver.session() as session:
            existing_user = session.read_transaction(get_user_by_email, email)
            if existing_user:
                flash("User already exists. Please log in.", "danger")
                return redirect(url_for("login"))

            # Create new user in Neo4j
            session.write_transaction(create_user, name, email, hashed_password)
            flash("Signup successful! Please log in.", "success")
            return redirect(url_for("login"))
        
    return render_template("signup.html")

def get_user_by_email(tx, email):
    query = "MATCH (u:User {email: $email}) RETURN u.id AS id, u.name AS name, u.email AS email"
    result = tx.run(query, email=email)
    return result.single()

def create_user(tx, name, email, hashed_password):
    query = """
    CREATE (u:User {id: $email, name: $name, email: $email, password: $password})
    """
    tx.run(query, email=email, name=name, password=hashed_password)

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
    
    return render_template("dashboard.html", name=current_user.name, fcs=fcs)

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

@app.route('/events', methods=['GET', 'POST'])
def events():
    if request.method == 'POST':
        # Get the event search and city selection from the form
        event_search = request.form.get('event-search', '')
        city = request.form.get('city-select', '')

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
        return render_template('events.html', events=results)

    except Exception as e:
        # Log exceptions for debugging
        print(f"Exception occurred: {e}")
        return render_template('events.html', events=[], error="Failed to load events.")



@app.route('/append-knowledge', methods=['POST'])
def append_knowledge():
    # Get the list of selected events from the form
    selected_events = request.form.getlist('selected_events')

    # Print the selected events to the console
    print("Selected Events:", selected_events)
    return render_template('dashboard.html')



# ---- Logout ----
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "success")
    return redirect(url_for("login"))

if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
