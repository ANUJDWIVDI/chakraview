from neo4j import GraphDatabase

class Neo4jHandler1:
    def __init__(self, uri, username, password):
        self.uri = uri
        self.username = username
        self.password = password
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def get_user_details(self, user_id):
        print(f"Getting details for user with ID: {user_id}")
        # Query Neo4j to get the user details based on user_id
        query = """
            MATCH (u:User {id: $user_id})
            RETURN u.name AS name, u.bio AS bio, u.occupation AS occupation, u.interests AS interests
        """
        with self.driver.session() as session:
            print("Running query...")
            result = session.run(query, user_id=user_id)
            user = result.single()
            print(user)

        if user:
            print("User found!")
            return {
                "name": user["name"],
                "bio": user["bio"],
                "occupation": user["occupation"],
                "interests": user["interests"]
            }
        else:
            print("User not found!")
            return {}
        

    def close(self):
        self.driver.close()
