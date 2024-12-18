import os
import json
import requests
from neo4j import GraphDatabase

# Neo4j Credentials and Setup
URI = "neo4j+s://608b8766.databases.neo4j.io"
AUTH = ("neo4j", "AZE3H4xpn9vP-Uwwz_H5fhiGSFZivlSvKGImf1ZoNjM")
driver = GraphDatabase.driver(URI, auth=AUTH)

# Gemma API Key
API_KEY = "AIzaSyBxTDsVQQoHkjOq4Qny5-7sOlvyna2f0E8"  # Use the provided API key here

# Function to extract text content from the uploaded document
def extract_text_from_document(document_path):
    # For simplicity, we assume the document is a text file. You can extend this to support PDFs, Word docs, etc.
    with open(document_path, "r") as file:
        content = file.read()
    return content

# Function to call Gemma API and generate Neo4j commands
def get_neo4j_commands_from_gemma(content):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={API_KEY}"
    payload = json.dumps({
        "contents": [
            {
                "parts": [
                    {
                        "text": "Prompt: Rooted in NitiSense's Strategic Inspiration AI-Powered Strategic Bot: NitiSense Inspired by the Arthashastra, where wisdom and strategy shaped victory, NitiSense is the AI-powered strategic assistant designed to lead startups through their journey with calculated insights and intelligence. NitiSense serves as a 24/7 mentor—providing clarity and real-time guidance. It suggests next steps to overcome growth bottlenecks, leveraging AI to propose partnerships, market exhibitions, and funding opportunities. Its market insights are deeply rooted in a profound understanding of global trends, similar to the strategic foresight described in ancient texts. Task for the AI: Purpose: Extract entities and relationships that reflect the interconnected nature of insights crucial for startup growth. Output Format: Return only the Neo4j CREATE NODE and CREATE RELATIONSHIP commands. This ensures the insights are actionable within the database. Avoid all explanations or additional text. Inspiration: Align the entity and relationship extraction with the mission of NitiSense—providing actionable, strategy-focused intelligence.."
                    },
                    {
                        "text": content
                    }
                ]
            }
        ]
    })
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, data=payload, headers=headers)
        response.raise_for_status()
        
        # Parse the response
        response_json = response.json()
        
        # Extract the relationship commands from the response
        commands = response_json['candidates'][0]['content']['parts'][0]['text']
        print(f"Gemma API Response Commands: {commands}")
        
        return commands
        
    except requests.exceptions.RequestException as e:
        print(f"Error calling Gemma API: {e}")
        return []

# Function to create nodes and relationships in Neo4j based on the returned commands
def create_relationships_in_neo4j(commands):
    session = driver.session()
    try:
        # Split the commands into individual lines (assuming each command is a separate line)
        for command in commands.split("\n"):
            command = command.strip()
            
            # Ignore empty commands
            if not command:
                continue
            
            # Check for "CREATE NODE" commands
            if command.startswith("CREATE NODE"):
                # Example: CREATE NODE (type:Document {content: 'some content'})
                with session.begin_transaction() as tx:
                    tx.run(command)
                    print(f"Created node: {command}")
            
            # Check for "CREATE RELATIONSHIP" commands
            elif command.startswith("CREATE RELATIONSHIP"):
                # Example: CREATE RELATIONSHIP (source:Document {content: 'some content'})-[:RELATED_TO]->(target:Document {content: 'some target content'})
                with session.begin_transaction() as tx:
                    tx.run(command)
                    print(f"Created relationship: {command}")
                
    except Exception as e:
        print(f"Error creating relationships in Neo4j: {e}")
    finally:
        session.close()

# Function to process the uploaded document and create relationships
def process_uploaded_document_and_create_relationships(document_content):
    # Step 1: Process the content in batches (if needed)
    batch_size = 2000  # Define batch size for content processing
    content_batches = [document_content[i:i+batch_size] for i in range(0, len(document_content), batch_size)]
    
    # Step 2: Send each batch of content to Gemma API
    for batch in content_batches:
        print(f"Processing batch of size {len(batch)} characters.")
        
        # Step 3: Get Neo4j commands from Gemma
        commands = get_neo4j_commands_from_gemma(batch)
        
        # Step 4: Create Neo4j nodes and relationships if commands are returned
        if commands:
            create_relationships_in_neo4j(commands)
        else:
            print("No Neo4j commands generated from Gemma API.")

