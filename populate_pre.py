import os
import json
import requests
from neo4j import GraphDatabase

# Neo4j Credentials and Setup
URI = "neo4j+s://608b8766.databases.neo4j.io"
AUTH = ("neo4j", "AZE3H4xpn9vP-Uwwz_H5fhiGSFZivlSvKGImf1ZoNjM")
driver = GraphDatabase.driver(URI, auth=AUTH)

# Gemini API Key
API_KEY = "AIzaSyBxTDsVQQoHkjOq4Qny5-7sOlvyna2f0E8"

# 50 prompts
prompts = [
    "Explain the concept of quantum entanglement and its potential implications.",
    "Analyze the historical and philosophical arguments for and against the existence of free will.",
    "Compare and contrast the economic systems of socialism, capitalism, and communism.",
    "Discuss the ethical considerations surrounding artificial intelligence development, including bias, job displacement, and the potential for misuse.",
    "Examine the impact of climate change on global biodiversity and human societies.",
    "Write a short story about a character who discovers they have the ability to travel through time.",
    "Compose a poem in the style of a famous poet, such as Shakespeare or Emily Dickinson.",
    "Create a fictional dialogue between two historical figures who never met, exploring a hypothetical conversation.",
    "Write a persuasive essay arguing for or against the use of space exploration funding.",
    "Compose a song lyric that captures the essence of a specific emotion, such as joy, sadness, or anger.",
    "Analyze the trends in global energy consumption over the past century and predict future challenges.",
    "Interpret a given set of statistical data on public health and draw meaningful conclusions.",
    "Examine the relationship between social media usage and mental health among adolescents.",
    "Analyze the impact of globalization on economic inequality within and between countries.",
    "Given a set of financial data, predict the potential for investment growth in a particular market.",
    "Explain the scientific method and its importance in conducting research.",
    "Analyze the ethical implications of gene editing technologies, such as CRISPR.",
    "Propose a solution to the problem of plastic pollution in the ocean.",
    "Explain the principles of thermodynamics and their applications in everyday life.",
    "Design an experiment to test the effectiveness of a new drug in treating a specific disease.",
    "Compare and contrast the social and political movements of the 1960s with contemporary social justice movements.",
    "Analyze the impact of colonialism on the cultural and economic development of a specific region.",
    "Discuss the significance of religious beliefs and practices in shaping human societies throughout history.",
    "Examine the role of art and literature in reflecting and influencing social and political change.",
    "Analyze the development of language and its impact on human communication and culture.",
    "Discuss the philosophical concepts of determinism and free will, and their implications for human behavior.",
    "Analyze the ethical implications of artificial intelligence, including issues of consciousness, sentience, and rights.",
    "Examine the concept of justice and its different interpretations throughout history and across cultures.",
    "Discuss the ethical considerations surrounding the use of animals in research and other industries.",
    "Analyze the concept of truth and its different forms, such as subjective truth, objective truth, and religious truth.",
    "Explain the principles of blockchain technology and its potential applications beyond cryptocurrency.",
    "Discuss the challenges and opportunities of renewable energy sources, such as solar, wind, and hydro power.",
    "Analyze the impact of the internet on human communication, social interaction, and the spread of information.",
    "Explain the principles of artificial intelligence, including machine learning, deep learning, and natural language processing.",
    "Design a solution to a real-world problem using engineering principles and technological innovation.",
    "Analyze the causes and consequences of poverty and inequality in modern societies.",
    "Discuss the role of education in promoting social mobility and reducing inequality.",
    "Examine the challenges and opportunities of immigration in a globalized world.",
    "Analyze the role of media in shaping public opinion and influencing political discourse.",
    "Discuss the ethical considerations surrounding the use of surveillance technologies by governments and corporations.",
    "Imagine a future where humans have colonized Mars. Describe the challenges and opportunities that this society would face.",
    "Invent a new technology that could revolutionize the way we live and work.",
]

# Helper function to summarize content
def summarize_content(content):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=" + API_KEY
    payload = json.dumps({
        "contents": [
            {
                "parts": [
                                        {
                        "text": "Please provide a very concise and summarized answer to the following question. Ensure that the key concepts are preserved while making it as short as possible."
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

# Helper function to save content to Neo4j
def save_to_neo4j(content, summarized_text, prompt):
    session = driver.session()
    
    try:
        with session.begin_transaction() as tx:
            tx.run("""
                CREATE (n:Document {content: $content, summary: $summary, prompt: $prompt})
            """, content=content, summary=summarized_text, prompt=prompt)
        
    except Exception as e:
        print(f"Error saving to Neo4j: {e}")
    finally:
        session.close()

# Iterate over all prompts, summarize and save to Neo4j
def process_prompts(prompts):
    for prompt in prompts:
        # Summarize the prompt (using prompt as content here for simplicity)
        summarized_text = summarize_content(prompt)

        # Save to Neo4j
        save_to_neo4j(prompt, summarized_text, prompt)

        print(f"Processed and saved prompt: {prompt}")

# Main execution
if __name__ == "__main__":
    process_prompts(prompts)
