import os
from flask import Flask, flash, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from dotenv import load_dotenv

app = Flask(__name__)

# Database configuration for MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234567890@localhost/gow'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

load_dotenv() 

# Mail configuration using environment variables for security
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL') == 'True'
mail = Mail(app)

# Define the Todo model
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, default=False)
    deadline_date = db.Column(db.String(10))
    deadline_time = db.Column(db.String(5))

    def as_dict(self):  
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    # todo = Todo(task="Buy milk", deadline_date="2023-03-15", deadline_time="14:00")
    # print(todo.as_dict())  # Output: {'id': None, 'task': 'gowtham', 'done': False, 'deadline_date': '2023-03-15', 'deadline_time': '14:00'}
    #Note that the id attribute is None because the todo item has not been saved to the

# Create the database
with app.app_context():
    db.create_all()

# Sample route to render the front-end template
@app.route('/')
def index():
    todos = Todo.query.all()
    return render_template('index.html', todos=todos)

# CRUD API endpoints
@app.route('/api/todos', methods=['GET', 'POST'])
def manage_todos():
    if request.method == 'POST':
        data = request.json
        new_todo = Todo(task=data['task'], deadline_date=data.get('deadline_date'), deadline_time=data.get('deadline_time'))
        db.session.add(new_todo)
        db.session.commit()
        return jsonify({'message': 'Todo created successfully'}), 201
    
    todos = Todo.query.all()
    return jsonify([todo.as_dict() for todo in todos])

@app.route('/api/todos/<int:id>', methods=['PUT', 'DELETE'])
def update_delete_todo(id):
    todo = Todo.query.get_or_404(id)
    
    if request.method == 'PUT':
        data = request.json
        todo.task = data.get('task', todo.task)
        todo.deadline_date = data.get('deadline_date', todo.deadline_date)
        todo.deadline_time = data.get('deadline_time', todo.deadline_time)
        todo.done = data.get('done', todo.done)
        db.session.commit()
        return jsonify({'message': 'Todo updated successfully'})
    
    db.session.delete(todo)
    db.session.commit()
    return jsonify({'message': 'Todo deleted successfully'})

@app.route('/api/todos/<int:id>/assign', methods=['POST'])
def assign_task(id):
    todo = Todo.query.get_or_404(id)
    data = request.json
    email = data.get('email')
    if not email:
        return jsonify({'message': 'Email is required'}), 400
    
    send_email_notification(email, todo.task)
    return jsonify({'message': 'Task assigned successfully'})

def send_email_notification(email, task):
    msg = Message('New Task Assigned', sender=os.getenv('MAIL_USERNAME'), recipients=[email])
    msg.body = f'You have been assigned a new task: \n{task}'
    try:
        mail.send(msg)
    except Exception as e:
        print(f'Failed to send email: {str(e)}')

if __name__ == '__main__':
    app.run(debug=True)
