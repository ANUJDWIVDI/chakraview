from neo4j import GraphDatabase

class Neo4jHandler:
    def __init__(self, uri, username, password):
        self.uri = uri
        self.username = username
        self.password = password
        self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))

    def search_users(self, query):
        """
        Fetch users based on the query. If no query is provided, fetch all users.
        """
        with self.driver.session() as session:
            if query:
                query_string = """
                    MATCH (u:User)
                    WHERE u.name CONTAINS $query
                    RETURN u.name AS name, 
                           u.bio AS bio, 
                           u.interests AS interests, 
                           u.occupation AS occupation,
                           u.fcs AS fcs
                """
                result = session.run(query_string, query=query)
            else:
                query_string = """
                    MATCH (u:User)
                    RETURN u.name AS name, 
                           u.bio AS bio, 
                           u.interests AS interests, 
                           u.occupation AS occupation,
                           u.fcs AS fcs
                """
                result = session.run(query_string)
        
            # Format the result into a list of dictionaries
            users = [
                {
                    "name": record.get("name", "N/A"),
                    "bio": record.get("bio", "N/A"),
                    "interests": record.get("interests", "N/A"),
                    "occupation": record.get("occupation", "N/A"),
                    "fcs": record.get("fcs", "N/A")
                }
                for record in result
            ]
        return users

    def update_user_interests(self, user_id, events):
        """
        Updates a user's interests in the Neo4j database by appending new events.
        """
        with self.driver.session() as session:
            # Begin a transaction
            session.write_transaction(self._append_interests, user_id, events)

    def _append_interests(self, tx, user_id, events):
        """
        Internal method to handle the update of interests.
        """
        query = """
        MERGE (user:User {id: $user_id})  // Find or create the User node by ID
        WITH user
        UNWIND $events AS event
        MERGE (e:Event {name: event})  // Find or create the Event node
        MERGE (user)-[r:INTERESTED_IN]->(e)  // Create the relationship if it does not already exist
        """
        tx.run(query, user_id=user_id, events=events)

    def close(self):
        """
        Close the Neo4j driver and session.
        """
        self.driver.close()
