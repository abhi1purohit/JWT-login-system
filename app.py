from flask import Flask,request,jsonify,make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
import jwt
import datetime
from functools import wraps

app=Flask(__name__)
app.config['SECRET_KEY']='abhishek'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

db=SQLAlchemy(app)


class User(db.Model):

    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(50))
    password=db.Column(db.String(50))
    todo=db.relationship('Todo',backref='user')


class Todo(db.Model):

    id=db.Column(db.Integer,primary_key=True)
    task=db.Column(db.String(50))
    completed=db.Column(db.Boolean())
    assigned_user_id=db.Column(db.Integer,db.ForeignKey('user.id'))


class Admin(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(50))
    password=db.Column(db.String(50))



def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message' : 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = Admin.query.filter_by(name=data['name']).first()
        except:
            return jsonify({'message' : 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated



@app.route('/user',methods=['POST'])
def createuser():
    data=request.get_json()
    new_user=User(name=data['name'],password=data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message':'new user created!'})

@app.route('/admin',methods=['POST'])
def createadmin():
    data=request.get_json()
    new_user=Admin(name=data['name'],password=data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message':'new admin created!'})


@app.route('/user', methods=['GET'])
def get_all_users():
    users=User.query.all()
    ra=[]
    for user in users:
        user_data={}
        user_data['name']=user.name
        user_data['password']=user.password
        user_data['todo']=user.todo
        ra.append(user_data)
    return jsonify({'users':ra})

@app.route('/admin', methods=['GET'])
def get_all_admin():
    ad=Admin.query.all()
    ra=[]
    for a in ad:
        user_data={}
        user_data['name']=a.name
        user_data['password']=a.password
        ra.append(user_data)
    return jsonify({'users':ra})

@app.route('/login')
def login():
    auth=request.authorization
    if not auth or not auth.username or not auth.password:
        return make_response('Not verified',401,{'WWW-Authenticate':'Basic realm="Login required!"'})
    user=Admin.query.filter_by(name=auth.username).first()
    if not user:
        return make_response('Not verified',401,{'WWW-Authenticate':'Basic realm="Login required!"'})
    else:
        token = jwt.encode({'name': user.name, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
    return jsonify({'token' : token.encode().decode('UTF-8')})



@app.route('/todo',methods=['GET'])
@token_required
def get_all_todos(current_user):
    todos = Todo.query.filter_by(user_id=current_user.id).all()
    output=[]
    for todo in todos:
        todo_data={}
        todo_data['id']=Todo.id
        todo_data['task']=todo.task
        todo_data['complete']=todo.completed
        output.append(todo_data)
    return jsonify({'todos':output})



@app.route('/todo', methods=['POST'])
@token_required
def create_todo():
    data = request.get_json()

    new_todo = Todo(task=data['task'], completed=False, assigned_user_id=data['assigned_user_id'])
    db.session.add(new_todo)
    db.session.commit()

    return jsonify({'message' : "Todo created!"})


@app.route('/todo/<todo_id>', methods=['PUT'])
@token_required
def complete_todo(current_user, todo_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id)

    if not todo:
        return jsonify({'message' : 'No todo found!'})

    todo.complete = True
    db.session.commit()

    return jsonify({'message' : 'Todo item has been completed!'})




if(__name__=='__main__'):
    app.run(debug=True)
