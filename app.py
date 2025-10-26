from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# NOTE: For deployment, consider using a persistent database like PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///event.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ----------------- MODELS -----------------
# Stores group information
class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # Stores user IDs (strings) that are members of the group
    members = db.Column(db.PickleType, default=[]) 
    # Stores the user ID (string) of the creator
    creator = db.Column(db.String(50), nullable=False) 

# Stores poll information associated with a group
class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    question = db.Column(db.String(200), nullable=False)
    # Stores a list of dictionaries, e.g., [{"text": "Option A", "votes": ["user1", "user2"]}]
    options = db.Column(db.PickleType, default=[])

# ----------------- ROUTES -----------------
@app.route('/')
def home():
    """Simple health check endpoint."""
    return jsonify({"message": "PlanPull backend connected and ready!"})

@app.route('/groups', methods=['POST'])
def create_group():
    """Creates a new group and returns its ID."""
    data = request.get_json()
    
    # Validate required fields
    if not data or 'name' not in data or 'creator' not in data:
        return jsonify({"message": "Invalid input: 'name' and 'creator' are required"}), 400
    
    # Ensure members list is used, defaulting to creator if not provided
    members_list = data.get('members', [data['creator']])
    if data['creator'] not in members_list:
         members_list.append(data['creator'])

    group = Group(name=data['name'], members=members_list, creator=data['creator'])
    db.session.add(group)
    db.session.commit()
    return jsonify({"message": "Group created", "group_id": group.id}), 201

@app.route('/polls', methods=['POST'])
def create_poll():
    """Creates a new poll associated with a group."""
    data = request.get_json()
    
    # Validate required fields
    if not data or 'group_id' not in data or 'question' not in data or 'options' not in data:
        return jsonify({"message": "Invalid input: 'group_id', 'question', and 'options' are required"}), 400
        
    group = Group.query.get(data['group_id'])
    if not group:
        return jsonify({"message": f"Group with ID {data['group_id']} not found"}), 404
        
    # Initialize options structure for the poll
    options = [{"text": opt.strip(), "votes": []} for opt in data['options']]

    poll = Poll(group_id=group.id, question=data['question'], options=options)
    db.session.add(poll)
    db.session.commit()
    return jsonify({"message": "Poll created", "poll_id": poll.id}), 201

@app.route('/polls/<int:poll_id>/vote', methods=['POST'])
def vote_poll(poll_id):
    """Allows a user to cast a vote on a poll option."""
    data = request.get_json()
    poll = Poll.query.get(poll_id)

    if not poll:
        return jsonify({"message": f"Poll with ID {poll_id} not found"}), 404
        
    # Validate input
    if 'user_id' not in data or 'option_index' not in data:
        return jsonify({"message": "Invalid input: 'user_id' and 'option_index' are required"}), 400

    user_id = data['user_id']
    option_index = data['option_index']
    
    # Check if option_index is valid
    if not (0 <= option_index < len(poll.options)):
        return jsonify({"message": "Invalid option index"}), 400

    # Ensure options list is mutable before modifying
    options = poll.options
    
    # Remove user's previous vote if one exists (Allows changing vote)
    for opt in options:
        if user_id in opt['votes']:
            opt['votes'].remove(user_id)
            
    # Add new vote
    options[option_index]['votes'].append(user_id)
    
    # Explicitly mark options as modified for SQLAlchemy to detect the change
    poll.options = options
    db.session.add(poll) # Add to session to mark as modified
    db.session.commit()
    
    return jsonify({"message": "Vote successfully cast/updated"}), 200

@app.route('/polls/<int:poll_id>', methods=['GET'])
def get_poll(poll_id):
    """Retrieves a specific poll's question and current votes."""
    poll = Poll.query.get(poll_id)
    if not poll:
        return jsonify({"message": f"Poll with ID {poll_id} not found"}), 404
        
    # Returns the question and the options list (which includes the vote counts)
    return jsonify({"question": poll.question, "options": poll.options}), 200


@app.route('/suggestions', methods=['POST'])
def get_suggestions():
    """
    Provides event/location suggestions based on location and mood.
    NOTE: This simulates an AI response to return a structured list.
    """
    data = request.get_json()
    if not data or 'location' not in data or 'mood' not in data:
        return jsonify({"message": "Invalid input: 'location' and 'mood' are required"}), 400

    location = data['location']
    mood = data['mood']
    
    # --- Simulated AI/Database Logic (Replace with actual LLM call if necessary) ---
    if mood == 'Energetic':
        suggestions = [
            {"name": "Sky Zone Trampoline Park", "description": f"Jump and burn energy near {location}! Great for a wild time."},
            {"name": "Local Dance Class (Salsa/Zumba)", "description": f"Find a quick drop-in class to move to the beat in {location}."},
            {"name": "Busy Downtown Food Market", "description": "High energy, fast pace, and lots of unique street food vendors."}
        ]
    elif mood == 'Relaxed':
        suggestions = [
            {"name": "Botanical Gardens or Quiet Park", "description": f"Perfect place to unwind and enjoy nature near {location}."},
            {"name": "Cozy Corner Bookstore/Cafe", "description": "Grab a hot drink and enjoy some light reading or quiet conversation."},
            {"name": "Meditation Center Drop-in", "description": "Find a local spot for deep relaxation and calm."}
        ]
    elif mood == 'Hungry':
         suggestions = [
            {"name": "Famous Local Diner", "description": f"Go where the locals go for the best comfort food in {location}."},
            {"name": "Taco Truck Alley/Street Food Hub", "description": "An adventure for the taste buds with plenty of options."},
            {"name": "All-You-Can-Eat Buffet", "description": "Satisfy any craving with unlimited options!"}
        ]
    elif mood == 'Creative':
         suggestions = [
            {"name": "Contemporary Art Museum", "description": f"Seek inspiration from abstract and modern works near {location}."},
            {"name": "DIY Pottery or Painting Studio", "description": "Hands-on fun to make something unique."},
            {"name": "Architecture Tour", "description": "Explore the unique buildings and design of the city center."}
        ]
    elif mood == 'Romantic':
         suggestions = [
            {"name": "Rooftop Restaurant with a View", "description": f"Dress up and enjoy a classy dinner overlooking {location}."},
            {"name": "Sunset Picnic Spot", "description": "Grab a blanket and some wine for a private, scenic experience."},
            {"name": "Stargazing at a Planetarium", "description": "A quiet, awe-inspiring place to share a moment."}
        ]
    else:
        # Fallback if an unexpected mood comes through
        suggestions = [
            {"name": "Local Public Library", "description": "Always a good place for a quiet break."},
            {"name": "Main Street Window Shopping", "description": "Just wander and see what catches your eye in the main area of the city."}
        ]

    return jsonify({"suggestions": suggestions}), 200


# ----------------- RUN APP -----------------
if __name__ == '__main__':
    with app.app_context():
        # Creates the database tables if they don't already exist
        db.create_all() 
    print("✅ PlanPull backend started successfully!")
    app.run(debug=True)
