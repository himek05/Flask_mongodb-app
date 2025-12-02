from flask import Flask, request, jsonify  # Import necessary modules from Flask
from pymongo import MongoClient  # Import MongoClient to interact with MongoDB
from datetime import datetime  # Import datetime to get the current time
import os  # Import os to access environment variables

# Initialize the Flask application
app = Flask(__name__)

# Set up the MongoDB client
# The MongoDB URI is fetched from the environment variable 'MONGODB_URI'
# For local development: 'mongodb://localhost:27017/'
# For Kubernetes with authentication: 'mongodb://username:password@mongodb:27017/'
mongodb_uri = os.environ.get(
    "MONGODB_URI",
    "mongodb://localhost:27017/"
)

try:
    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
    # Verify connection
    client.server_info()
    print(f"Successfully connected to MongoDB at {mongodb_uri}")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    client = None

# Connect to the database named 'flask_db'
db = client.flask_db if client else None
# Connect to the collection named 'data' within the 'flask_db' database
collection = db.data if db else None


# Define the route for the root URL
@app.route('/')
def index():
    # Return a welcome message with the current time
    return f"Welcome to the Flask app! The current time is: {datetime.now()}"


# Define the route for the '/data' endpoint
# This endpoint supports both GET and POST methods
@app.route('/data', methods=['GET', 'POST'])
def data():
    if collection is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    if request.method == 'POST':
        # If the request method is POST, get the JSON data from the request
        data = request.get_json()
        # Insert the data into the 'data' collection in MongoDB
        result = collection.insert_one(data)
        # Return a success message with status code 201 (Created)
        return jsonify({"status": "Data inserted", "id": str(result.inserted_id)}), 201
    elif request.method == 'GET':
        # If the request method is GET, retrieve all documents from the 'data' collection
        # Convert the documents to a list, excluding the '_id' field
        data = list(collection.find({}, {"_id": 0}))
        # Return the data as a JSON response with status code 200 (OK)
        return jsonify(data), 200


# Health check endpoint for Kubernetes readiness and liveness probes
@app.route('/health')
def health():
    if collection is None:
        return jsonify({"status": "unhealthy"}), 503
    try:
        # Try to execute a simple query to ensure database connectivity
        collection.find_one()
        return jsonify({"status": "healthy"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 503


# Run the Flask application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
