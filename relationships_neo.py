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

# Function to extract content and nodes from Neo4j
def extract_from_neo4j():
    session = driver.session()
    try:
        # Query to get all content nodes (example query, adjust as needed)
        result = session.run("MATCH (n:Document) RETURN n.content, n.summary, n.prompt LIMIT 10")
        content_list = []
        for record in result:
            content_list.append({
                "content": record["n.content"],
                "summary": record["n.summary"],
                "prompt": record["n.prompt"]
            })
        print(f"Extracted {len(content_list)} documents from Neo4j.")
        return content_list
    except Exception as e:
        print(f"Error extracting from Neo4j: {e}")
        return []
    finally:
        session.close()

# Function to call Gemma API and generate Neo4j commands (strictly code only)
def get_neo4j_commands_from_gemma(content):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={API_KEY}"
    payload = json.dumps({
        "contents": [
            {
                "parts": [
                    {
                        "text": "Extract all possible relationships and entities from the following content. Return ONLY the Neo4j code (CREATE NODE and CREATE RELATIONSHIP commands). Do not include any explanation or additional text. Only return executable code."
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

# Process content from Neo4j, get Neo4j commands from Gemma, and create relationships in Neo4j
def process_content_and_create_relationships():
    content_list = extract_from_neo4j()
    
    for node in content_list:
        content = node["content"]
        print(f"Processing content: {content[:100]}...")  # Print the first 100 chars of content
        
        # Get Neo4j commands from Gemma API
        commands = get_neo4j_commands_from_gemma(content)
        
        # If commands are found, create nodes and relationships in Neo4j
        if commands:
            create_relationships_in_neo4j(commands)
        else:
            print("No Neo4j commands generated from Gemma API.")
    
# Main execution
if __name__ == "__main__":
    process_content_and_create_relationships()


"""Extracted 10 documents from Neo4j.
Processing content: The Arthashastra, an ancient Indian treatise on statecraft and economics, offers valuable insights i...
Gemma API Response Commands: ```cypher
CREATE (a:Book {title: "Arthashastra"})
CREATE (eb:Concept {name: "Economic Prosperity"})
CREATE (s:Concept {name: "State"})
CREATE (c:Concept {name: "Citizens"})
CREATE (ns:Concept {name: "National Security"})
CREATE (ss:Concept {name: "Social Stability"})
CREATE (ip:Concept {name: "Individual Prosperity"})
CREATE (r:Concept {name: "Regulation"})
CREATE (p:Concept {name: "Promotion"})
CREATE (ea:Concept {name: "Economic Activities"})
CREATE (ftp:Concept {name: "Fair Trade Practices"})
CREATE (pci:Concept {name: "Protection of Consumer Interests"})
CREATE (ei:Concept {name: "Essential Infrastructure"})
CREATE (ag:Concept {name: "Agriculture"})
CREATE (eap:Concept {name: "Efficient Agricultural Practices"})
CREATE (is:Concept {name: "Irrigation Systems"})
CREATE (dap:Concept {name: "Fair Distribution of Agricultural Produce"})
CREATE (tc:Concept {name: "Trade and Commerce"})
CREATE (eg:Concept {name: "Economic Growth"})
CREATE (dt:Concept {name: "Domestic Trade"})
CREATE (it:Concept {name: "International Trade"})
CREATE (m:Concept {name: "Merchants"})
CREATE (str:Concept {name: "Safe Trade Routes"})
CREATE (im:Concept {name: "Industry and Manufacturing"})
CREATE (sl:Concept {name: "Skilled Labor"})
CREATE (ti:Concept {name: "Technological Innovation"})
CREATE (gs:Concept {name: "Government Support"})
CREATE (fm:Concept {name: "Financial Management"})
CREATE (b:Concept {name: "Budgeting"})
CREATE (t:Concept {name: "Taxation"})
CREATE (pmf:Concept {name: "Management of Public Finances"})
CREATE (ebp:Concept {name: "Ethical Business Practices"})
CREATE (h:Concept {name: "Honesty"})
CREATE (f:Concept {name: "Fairness"})
CREATE (tr:Concept {name: "Transparency"})
CREATE (fa:Concept {name: "Fraudulent Activities"})
CREATE (fc:Concept {name: "Fair Competition"})
CREATE (hcd:Concept {name: "Human Capital Development"})
CREATE (e:Concept {name: "Education"})
CREATE (tr2:Concept {name: "Training"})
CREATE (sd:Concept {name: "Skill Development"})
CREATE (wp:Concept {name: "Workforce Productivity"})
CREATE (id:Concept {name: "Infrastructure Development"})
CREATE (r2:Concept {name: "Roads"})
CREATE (br:Concept {name: "Bridges"})
CREATE (cn:Concept {name: "Communication Networks"})
CREATE (rm:Concept {name: "Resource Management"})
CREATE (cnr:Concept {name: "Conservation of Natural Resources"})
CREATE (ped:Concept {name: "Prevention of Environmental Degradation"})
CREATE (i:Concept {name: "Innovation"})
CREATE (ta:Concept {name: "Technological Advancement"})
CREATE (ir:Concept {name: "International Relations"})
CREATE (ec:Concept {name: "Economic Cooperation"})
CREATE (sw:Concept {name: "Social Welfare"})
CREATE (la:Concept {name: "Law and Order"})
CREATE (ljs:Concept {name: "Legal and Judicial System"})
CREATE (pr:Concept {name: "Property Rights"})
CREATE (lg:Concept {name: "Leadership and Governance"})
CREATE (mr:Concept {name: "Market Regulation"})
CREATE (ump:Concept {name: "Unfair Market Practices"})
CREATE (cp:Concept {name: "Consumer Protection"})
CREATE (rm2:Concept {name: "Risk Management"})
CREATE (pd:Concept {name: "Prudent Decision-Making"})
CREATE (cp2:Concept {name: "Contingency Planning"})
CREATE (csr:Concept {name: "Corporate Social Responsibility"})
CREATE (mbp:Concept {name: "Modern Business Practices"})
CREATE (a)-[:EMPHASIZES]->(eb)
CREATE (eb)-[:CONTRIBUTES_TO]->(ns)
CREATE (eb)-[:CONTRIBUTES_TO]->(ss)
CREATE (eb)-[:CONTRIBUTES_TO]->(ip)
CREATE (a)-[:DISCUSSES]->(s)
CREATE (s)-[:REGULATES]->(ea)
CREATE (s)-[:PROMOTES]->(ea)
CREATE (a)-[:EMPHASIZES]->(ftp)
CREATE (a)-[:EMPHASIZES]->(pci)
CREATE (a)-[:EMPHASIZES]->(ei)
CREATE (a)-[:EMPHASIZES]->(ag)
CREATE (ag)-[:REQUIRES]->(eap)
CREATE (ag)-[:REQUIRES]->(is)
CREATE (ag)-[:REQUIRES]->(dap)
CREATE (a)-[:EMPHASIZES]->(tc)
CREATE (tc)-[:PROMOTES]->(eg)
CREATE (tc)-[:INCLUDES]->(dt)
CREATE (tc)-[:INCLUDES]->(it)
CREATE (tc)-[:INCLUDES]->(m)
CREATE (tc)-[:REQUIRES]->(str)
CREATE (a)-[:EMPHASIZES]->(im)
CREATE (im)-[:REQUIRES]->(sl)
CREATE (im)-[:REQUIRES]->(ti)
CREATE (im)-[:REQUIRES]->(gs)
CREATE (a)-[:EMPHASIZES]->(fm)
CREATE (fm)-[:INCLUDES]->(b)
CREATE (fm)-[:INCLUDES]->(t)
CREATE (fm)-[:INCLUDES]->(pmf)
CREATE (a)-[:EMPHASIZES]->(ebp)
CREATE (ebp)-[:INCLUDES]->(h)
CREATE (ebp)-[:INCLUDES]->(f)
CREATE (ebp)-[:INCLUDES]->(tr)
CREATE (ebp)-[:OPPOSES]->(fa)
CREATE (ebp)-[:PROMOTES]->(fc)
CREATE (a)-[:EMPHASIZES]->(hcd)
CREATE (hcd)-[:INCLUDES]->(e)
CREATE (hcd)-[:INCLUDES]->(tr2)
CREATE (hcd)-[:INCLUDES]->(sd)
CREATE (hcd)-[:IMPROVES]->(wp)
CREATE (a)-[:EMPHASIZES]->(id)
CREATE (id)-[:INCLUDES]->(r2)
CREATE (id)-[:INCLUDES]->(br)
CREATE (id)-[:INCLUDES]->(cn)
CREATE (a)-[:EMPHASIZES]->(rm)
CREATE (rm)-[:INCLUDES]->(cnr)
CREATE (rm)-[:INCLUDES]->(ped)
CREATE (a)-[:EMPHASIZES]->(i)
CREATE (a)-[:EMPHASIZES]->(ta)
CREATE (a)-[:EMPHASIZES]->(ir)
CREATE (ir)-[:PROMOTES]->(ec)
CREATE (a)-[:EMPHASIZES]->(sw)
CREATE (a)-[:EMPHASIZES]->(la)
CREATE (la)-[:REQUIRES]->(ljs)
CREATE (la)-[:PROTECTS]->(pr)
CREATE (a)-[:EMPHASIZES]->(lg)
CREATE (lg)-[:PROMOTES]->(eg)
CREATE (a)-[:EMPHASIZES]->(mr)
CREATE (mr)-[:PREVENTS]->(ump)
CREATE (a)-[:EMPHASIZES]->(cp)
CREATE (a)-[:EMPHASIZES]->(rm2)
CREATE (rm2)-[:INCLUDES]->(pd)
CREATE (rm2)-[:INCLUDES]->(cp2)
CREATE (a)-[:SUGGESTS]->(csr)
CREATE (a)-[:RELEVANT_TO]->(mbp)

```

Processing content: Error: No summary found in the response....
Gemma API Response Commands: Please provide the content you wish to extract relationships and entities from.

Processing content: The Arthashastra, an ancient Indian treatise on statecraft and economics, offers valuable insights i...
Gemma API Response Commands: ```cypher
CREATE (a:Book {title:"Arthashastra"})
CREATE (eb:Concept {name:"Economic Prosperity"})
CREATE (state:Entity {name:"State"})
CREATE (citizen:Entity {name:"Citizen"})
CREATE (economy:Concept {name:"Strong Economy"})
CREATE (security:Concept {name:"National Security"})
CREATE (stability:Concept {name:"Social Stability"})
CREATE (prosperity:Concept {name:"Individual Prosperity"})
CREATE (r1:Emphasizes {description:"Emphasizes"})-[:RELATES_TO]->(a)
CREATE (r1)-[:RELATES_TO]->(eb)
CREATE (r1)-[:RELATES_TO]->(state)
CREATE (r1)-[:RELATES_TO]->(citizen)
CREATE (r2:Emphasizes {description:"Emphasizes"})-[:RELATES_TO]->(a)
CREATE (r2)-[:RELATES_TO]->(economy)
CREATE (r2)-[:RELATES_TO]->(security)
CREATE (r2)-[:RELATES_TO]->(stability)
CREATE (r2)-[:RELATES_TO]->(prosperity)
CREATE (role:Concept {name:"Role of State"})
CREATE (regulation:Concept {name:"Economic Regulation"})
CREATE (promotion:Concept {name:"Economic Promotion"})
CREATE (fairTrade:Concept {name:"Fair Trade Practices"})
CREATE (consumerProtection:Concept {name:"Consumer Protection"})
CREATE (infrastructure:Concept {name:"Essential Infrastructure"})
CREATE (growth:Concept {name:"Economic Growth"})
CREATE (r3:Highlights {description:"Highlights"})-[:RELATES_TO]->(a)
CREATE (r3)-[:RELATES_TO]->(role)
CREATE (r3)-[:RELATES_TO]->(regulation)
CREATE (r3)-[:RELATES_TO]->(promotion)
CREATE (r3)-[:RELATES_TO]->(fairTrade)
CREATE (r3)-[:RELATES_TO]->(consumerProtection)
CREATE (r3)-[:RELATES_TO]->(infrastructure)
CREATE (r3)-[:RELATES_TO]->(growth)
CREATE (agriculture:Concept {name:"Agriculture"})
CREATE (backbone:Concept {name:"Backbone of Economy"})
CREATE (efficientPractices:Concept {name:"Efficient Agricultural Practices"})
CREATE (irrigation:Concept {name:"Irrigation Systems"})
CREATE (distribution:Concept {name:"Fair Distribution"})
CREATE (produce:Concept {name:"Agricultural Produce"})
CREATE (r4:Recognizes {description:"Recognizes"})-[:RELATES_TO]->(a)
CREATE (r4)-[:RELATES_TO]->(agriculture)
CREATE (r4)-[:RELATES_TO]->(backbone)
CREATE (r4)-[:RELATES_TO]->(efficientPractices)
CREATE (r4)-[:RELATES_TO]->(irrigation)
CREATE (r4)-[:RELATES_TO]->(distribution)
CREATE (r4)-[:RELATES_TO]->(produce)
CREATE (trade:Concept {name:"Trade and Commerce"})
CREATE (domesticTrade:Concept {name:"Domestic Trade"})
CREATE (internationalTrade:Concept {name:"International Trade"})
CREATE (merchants:Entity {name:"Merchants"})
CREATE (tradeRoutes:Concept {name:"Safe Trade Routes"})
CREATE (r5:Acknowledges {description:"Acknowledges"})-[:RELATES_TO]->(a)
CREATE (r5)-[:RELATES_TO]->(trade)
CREATE (r5)-[:RELATES_TO]->(domesticTrade)
CREATE (r5)-[:RELATES_TO]->(internationalTrade)
CREATE (r5)-[:RELATES_TO]->(merchants)
CREATE (r5)-[:RELATES_TO]->(tradeRoutes)
CREATE (industry:Concept {name:"Industry and Manufacturing"})
CREATE (skilledLabor:Concept {name:"Skilled Labor"})
CREATE (innovation:Concept {name:"Technological Innovation"})
CREATE (governmentSupport:Concept {name:"Government Support"})
CREATE (r6:Recognizes {description:"Recognizes"})-[:RELATES_TO]->(a)
CREATE (r6)-[:RELATES_TO]->(industry)
CREATE (r6)-[:RELATES_TO]->(skilledLabor)
CREATE (r6)-[:RELATES_TO]->(innovation)
CREATE (r6)-[:RELATES_TO]->(governmentSupport)
CREATE (financialManagement:Concept {name:"Financial Management"})
CREATE (budgeting:Concept {name:"Budgeting"})
CREATE (taxation:Concept {name:"Taxation"})
CREATE (publicFinances:Concept {name:"Public Finances"})
CREATE (r7:Emphasizes {description:"Emphasizes"})-[:RELATES_TO]->(a)
CREATE (r7)-[:RELATES_TO]->(financialManagement)
CREATE (r7)-[:RELATES_TO]->(budgeting)
CREATE (r7)-[:RELATES_TO]->(taxation)
CREATE (r7)-[:RELATES_TO]->(publicFinances)
CREATE (ethicalPractices:Concept {name:"Ethical Business Practices"})
CREATE (honesty:Concept {name:"Honesty"})
CREATE (fairness:Concept {name:"Fairness"})
CREATE (transparency:Concept {name:"Transparency"})
CREATE (fraudulentActivities:Concept {name:"Fraudulent Activities"})
CREATE (fairCompetition:Concept {name:"Fair Competition"})
CREATE (r8:Emphasizes {description:"Emphasizes"})-[:RELATES_TO]->(a)
CREATE (r8)-[:RELATES_TO]->(ethicalPractices)
CREATE (r8)-[:RELATES_TO]->(honesty)
CREATE (r8)-[:RELATES_TO]->(fairness)
CREATE (r8)-[:RELATES_TO]->(transparency)
CREATE (r8)-[:RELATES_TO]->(fraudulentActivities)
CREATE (r8)-[:RELATES_TO]->(fairCompetition)
CREATE (humanCapital:Concept {name:"Human Capital Development"})
CREATE (education:Concept {name:"Education"})
CREATE (training:Concept {name:"Training"})
CREATE (skillDevelopment:Concept {name:"Skill Development"})
CREATE (productivity:Concept {name:"Workforce Productivity"})
CREATE (r9:Recognizes {description:"Recognizes"})-[:RELATES_TO]->(a)
CREATE (r9)-[:RELATES_TO]->(humanCapital)
CREATE (r9)-[:RELATES_TO]->(education)
CREATE (r9)-[:RELATES_TO]->(training)
CREATE (r9)-[:RELATES_TO]->(skillDevelopment)
CREATE (r9)-[:RELATES_TO]->(productivity)
CREATE (infrastructureDevelopment:Concept {name:"Infrastructure Development"})
CREATE (roads:Concept {name:"Roads"})
CREATE (bridges:Concept {name:"Bridges"})
CREATE (communicationNetworks:Concept {name:"Communication Networks"})
CREATE (r10:Recognizes {description:"Recognizes"})-[:RELATES_TO]->(a)
CREATE (r10)-[:RELATES_TO]->(infrastructureDevelopment)
CREATE (r10)-[:RELATES_TO]->(roads)
CREATE (r10)-[:RELATES_TO]->(bridges)
CREATE (r10)-[:RELATES_TO]->(communicationNetworks)
CREATE (resourceManagement:Concept {name:"Sustainable Resource Management"})
CREATE (conservation:Concept {name:"Conservation"})
CREATE (environmentalDegradation:Concept {name:"Environmental Degradation"})
CREATE (r11:Emphasizes {description:"Emphasizes"})-[:RELATES_TO]->(a)
CREATE (r11)-[:RELATES_TO]->(resourceManagement)
CREATE (r11)-[:RELATES_TO]->(conservation)
CREATE (r11)-[:RELATES_TO]->(environmentalDegradation)
CREATE (innovationTechnology:Concept {name:"Innovation and Technology"})
CREATE (economicProgress:Concept {name:"Economic Progress"})
CREATE (r12:Recognizes {description:"Recognizes"})-[:RELATES_TO]->(a)
CREATE (r12)-[:RELATES_TO]->(innovationTechnology)
CREATE (r12)-[:RELATES_TO]->(economicProgress)
CREATE (internationalRelations:Concept {name:"International Relations"})
CREATE (economicCooperation:Concept {name:"Economic Cooperation"})
CREATE (r13:Recognizes {description:"Recognizes"})-[:RELATES_TO]->(a)
CREATE (r13)-[:RELATES_TO]->(internationalRelations)
CREATE (r13)-[:RELATES_TO]->(economicCooperation)
CREATE (socialWelfare:Concept {name:"Social Welfare Programs"})
CREATE (r14:Emphasizes {description:"Emphasizes"})-[:RELATES_TO]->(a)
CREATE (r14)-[:RELATES_TO]->(socialWelfare)
CREATE (lawOrder:Concept {name:"Law and Order"})
CREATE (legalSystem:Concept {name:"Legal and Judicial System"})
CREATE (propertyRights:Concept {name:"Property Rights"})
CREATE (r15:Emphasizes {description:"Emphasizes"})-[:RELATES_TO]->(a)
CREATE (r15)-[:RELATES_TO]->(lawOrder)
CREATE (r15)-[:RELATES_TO]->(legalSystem)
CREATE (r15)-[:RELATES_TO]->(propertyRights)
CREATE (leadershipGovernance:Concept {name:"Leadership and Governance"})
CREATE (r16:Emphasizes {description:"Emphasizes"})-[:RELATES_TO]->(a)
CREATE (r16)-[:RELATES_TO]->(leadershipGovernance)
CREATE (marketRegulation:Concept {name:"Market Regulation"})
CREATE (governmentIntervention:Concept {name:"Government Intervention"})
CREATE (unfairPractices:Concept {name:"Unfair Practices"})
CREATE (monopolies:Concept {name:"Monopolies"})
CREATE (priceGouging:Concept {name:"Price Gouging"})
CREATE (r17:Recognizes {description:"Recognizes"})-[:RELATES_TO]->(a)
CREATE (r17)-[:RELATES_TO]->(marketRegulation)
CREATE (r17)-[:RELATES_TO]->(governmentIntervention)
CREATE (r17)-[:RELATES_TO]->(unfairPractices)
CREATE (r17)-[:RELATES_TO]->(monopolies)
CREATE (r17)-[:RELATES_TO]->(priceGouging)
CREATE (consumerInterests:Concept {name:"Consumer Interests"})
CREATE (goodsServices:Concept {name:"Goods and Services"})
CREATE (r18:Emphasizes {description:"Emphasizes"})-[:RELATES_TO]->(a)
CREATE (r18)-[:RELATES_TO]->(consumerInterests)
CREATE (r18)-[:RELATES_TO]->(goodsServices)
CREATE (riskManagement:Concept {name:"Risk Management"})
CREATE (prudentDecisionMaking:Concept {name:"Prudent Decision-Making"})
CREATE (contingencyPlanning:Concept {name:"Contingency Planning"})
CREATE (r19:Recognizes {description:"Recognizes"})-[:RELATES_TO]->(a)
CREATE (r19)-[:RELATES_TO]->(riskManagement)
CREATE (r19)-[:RELATES_TO]->(prudentDecisionMaking)
CREATE (r19)-[:RELATES_TO]->(contingencyPlanning)
CREATE (corporateSocialResponsibility:Concept {name:"Corporate Social Responsibility"})
CREATE (ethicalConduct:Concept {name:"Ethical Conduct"})
CREATE (socialResponsibility:Concept {name:"Social Responsibility"})
CREATE (r20:Suggests {description:"Suggests"})-[:RELATES_TO]->(a)
CREATE (r20)-[:RELATES_TO]->(corporateSocialResponsibility)
CREATE (r20)-[:RELATES_TO]->(ethicalConduct)
CREATE (r20)-[:RELATES_TO]->(socialResponsibility)
CREATE (modernRelevance:Concept {name:"Relevance to Modern Business"})
CREATE (r21:Maintains {description:"Maintains"})-[:RELATES_TO]->(a)
CREATE (r21)-[:RELATES_TO]->(modernRelevance)

```

Processing content: Explain the concept of quantum entanglement and its potential implications....
Gemma API Response Commands: ```cypher
CREATE (c1:Concept {name:'Quantum Entanglement'})
CREATE (c2:Concept {name:'Quantum Mechanics'})
CREATE (c3:Concept {name:'Potential Implications'})
CREATE (c4:Concept {name:'Spooky Action'})
CREATE (r1:HAS_CONCEPT {weight:1})-[r1]->(c1)<-[r2:IS_A_PART_OF {weight:1}]-(c2)
CREATE (r3:HAS_CONCEPT {weight:1})-[r3]->(c1)<-[r4:HAS_CONCEPT {weight:1}]-(c3)
CREATE (r5:IS_DESCRIBED_AS {weight:1})-[r5]->(c1)<-[r6:HAS_ATTRIBUTE {weight:1}]-(c4)

```

Processing content: Analyze the historical and philosophical arguments for and against the existence of free will....
Gemma API Response Commands: ```cypher
CREATE (a:Concept {name:'Free Will'})
CREATE (b:Argument {name:'Historical Arguments For Free Will'})
CREATE (c:Argument {name:'Historical Arguments Against Free Will'})
CREATE (d:Argument {name:'Philosophical Arguments For Free Will'})
CREATE (e:Argument {name:'Philosophical Arguments Against Free Will'})
CREATE (a)-[:HAS_ARGUMENT]->(b)
CREATE (a)-[:HAS_ARGUMENT]->(c)
CREATE (a)-[:HAS_ARGUMENT]->(d)
CREATE (a)-[:HAS_ARGUMENT]->(e)

```

Processing content: Compare and contrast the economic systems of socialism, capitalism, and communism....
Gemma API Response Commands: ```cypher
CREATE (s:EconomicSystem {name: 'Socialism'})
CREATE (c:EconomicSystem {name: 'Capitalism'})
CREATE (co:EconomicSystem {name: 'Communism'})

CREATE (s)-[:CONTRASTS_WITH]->(c)
CREATE (s)-[:CONTRASTS_WITH]->(co)
CREATE (c)-[:CONTRASTS_WITH]->(co)
CREATE (s)-[:COMPARES_WITH]->(c)
CREATE (s)-[:COMPARES_WITH]->(co)
CREATE (c)-[:COMPARES_WITH]->(co)

```

Processing content: Discuss the ethical considerations surrounding artificial intelligence development, including bias, ...
Gemma API Response Commands: ```cypher
CREATE (a:Topic {name:'Artificial Intelligence Development'})
CREATE (b:EthicalConsideration {name:'Bias'})
CREATE (c:EthicalConsideration {name:'Job Displacement'})
CREATE (d:EthicalConsideration {name:'Potential for Misuse'})
CREATE (a)-[:HAS_ETHICAL_CONSIDERATION]->(b)
CREATE (a)-[:HAS_ETHICAL_CONSIDERATION]->(c)
CREATE (a)-[:HAS_ETHICAL_CONSIDERATION]->(d)

```

Processing content: Examine the impact of climate change on global biodiversity and human societies....
Gemma API Response Commands: ```cypher
CREATE (c:Concept {name: 'Climate Change'})
CREATE (b:Concept {name: 'Biodiversity'})
CREATE (h:Concept {name: 'Human Societies'})
CREATE (i:Impact {name: 'Impact'})

CREATE (c)-[:AFFECTS]->(b)
CREATE (c)-[:AFFECTS]->(h)
CREATE (c)-[:CAUSES]->(i)
CREATE (i)-[:ON]->(b)
CREATE (i)-[:ON]->(h)

```

Processing content: Write a short story about a character who discovers they have the ability to travel through time....
Gemma API Response Commands: ```cypher
CREATE (p:Person {name: "Alice"})
CREATE (a:Ability {name: "Time Travel"})
CREATE (t:Time {period: "Past"})
CREATE (f:Time {period: "Future"})
CREATE (p)-[:POSSESSES]->(a)
CREATE (p)-[:TRAVELS_TO]->(t)
CREATE (p)-[:TRAVELS_TO]->(f)

```

Processing content: Compose a poem in the style of a famous poet, such as Shakespeare or Emily Dickinson....
Gemma API Response Commands: ```cypher
CREATE (p:Poem {title:"Untitled", style:"Shakespearean"})
CREATE (e:Entity {name:"Speaker"})
CREATE (e2:Entity {name:"Beloved"})
CREATE (e3:Entity {name:"Time"})
CREATE (e4:Entity {name:"Rose"})
CREATE (r:RelatesTo {description:"expresses feelings for"})
CREATE (p)-[r]->(e2)
CREATE (r2:RelatesTo {description:"reflects on"})
CREATE (p)-[r2]->(e3)
CREATE (r3:Symbol {description:"represents beauty"})
CREATE (p)-[r3]->(e4)
CREATE (r4:RelatesTo {description:"addresses"})
CREATE (p)-[r4]->(e)

```"""