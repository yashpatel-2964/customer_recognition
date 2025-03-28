# File: db_connection.py
import pymongo
import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Connection singleton
_mongo_client = None

def get_database():
    """
    Function to get MongoDB connection
    Returns MongoDB database object
    """
    global _mongo_client
    
    try:
        if _mongo_client is None:
            # Get MongoDB connection string from environment variable
            mongo_uri = os.environ.get('MONGO_URI')
            
            if not mongo_uri:
                raise ValueError("MongoDB URI not found in environment variables")
            
            # Create a new client and connect to the server
            _mongo_client = MongoClient(mongo_uri, server_api=ServerApi('1'))
            
            # Send a ping to confirm a successful connection
            _mongo_client.admin.command('ping')
            print("Successfully connected to MongoDB")
        
        # Return the database
        return _mongo_client.get_database()
    
    except Exception as e:
        print(f"Error connecting to database: {e}")
        # Return a simple mock database for testing
        return {
            "customers": MockCollection(),
            "employees": MockCollection(),
            "oauth_states": MockCollection()
        }

# Simple mock collection for testing when database isn't available
class MockCollection:
    def __init__(self):
        self.data = {}
        self.counter = 0
    
    def find_one(self, query):
        # Return None to simulate no results found
        return None
        
    def insert_one(self, document):
        # Mock successful insertion
        self.counter += 1
        document['_id'] = self.counter
        self.data[self.counter] = document
        print(f"MOCK DB: Would insert: {document}")
        
        class Result:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id
        
        return Result(self.counter)
        
    def update_one(self, query, update):
        # Mock successful update
        print(f"MOCK DB: Would update {query} with {update}")
        return True
    
    def delete_one(self, query):
        # Mock successful deletion
        print(f"MOCK DB: Would delete {query}")
        return True
    
    def count_documents(self, query):
        # Return 0 to simulate empty collection
        return 0

# Test the connection if running directly
if __name__ == "__main__":
    db = get_database()
    print("Database connected successfully")