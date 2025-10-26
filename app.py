from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///event.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ----------------- MODELS -----------------
class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    members = db.Column(db.PickleType, default=[])
    creator = db.Column(db.Integer, nullable=False)

class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    question = db.Column(db.String(200), nullable=False)
    options = db.Column(db.PickleType, default=[])

# ----------------- ROUTES -----------------
@app.route('/')
def home():
    return jsonify({"message": "PlanPull backend connected to database!"})

@app.route('/groups', methods=['POST'])
def create_group():
    data = request.get_json()
    if not data or 'name' not in data or 'creator' not in data:
        return jsonify({"message": "Invalid input"}), 400

    group = Group(name=data['name'], members=data.get('members', []), creator=data['creator'])
    db.session.add(group)
    db.session.commit()
    return jsonify({"message": "Group created", "group_id": group.id})

@app.route('/polls', methods=['POST'])
def create_poll():
    data = request.get_json()
    group = Group.query.get(data['group_id'])
    if not group:
        return jsonify({"message": "Group not found"}), 404

    options = [{"text": opt, "votes": []} for opt in data['options']]
    poll = Poll(group_id=group.id, question=data['question'], options=options)
    db.session.add(poll)
    db.session.commit()
    return jsonify({"message": "Poll created", "poll_id": poll.id})

@app.route('/polls/<int:poll_id>/vote', methods=['POST'])
def vote_poll(poll_id):
    data = request.get_json()
    poll = Poll.query.get(poll_id)
    if not poll:
        return jsonify({"message": "Poll not found"}), 404

    user_id = data['user_id']
    option_index = data['option_index']

    # Check if user already voted
    for opt in poll.options:
        if user_id in opt['votes']:
            return jsonify({"message": "User already voted"}), 400

    poll.options[option_index]['votes'].append(user_id)
    db.session.commit()
    return jsonify({"message": "Vote added", "options": poll.options})

@app.route('/polls/<int:poll_id>', methods=['GET'])
def get_poll(poll_id):
    poll = Poll.query.get(poll_id)
    if not poll:
        return jsonify({"message": "Poll not found"}), 404

    return jsonify({
        "question": poll.question,
        "options": poll.options
    })

# ----------------- RUN APP -----------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("✅ PlanPull backend started successfully!")
    app.run(debug=True)
