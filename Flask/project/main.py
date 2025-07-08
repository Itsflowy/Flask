####
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime 


app=Flask(__name__, template_folder="templates", static_folder="static")
app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///test.db"
database=SQLAlchemy(app) 
locks=True

class Users(database.Model):
    id=database.Column(database.Integer, primary_key=True) 
    email=database.Column(database.String(100), unique=True)
    password=database.Column(database.String(50), nullable=True)
    data = database.Column(database.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"users{self.id}"
class Profiles(database.Model):
    id= database.Column(database.Integer, primary_key=True)
    name=database.Column(database.String(50), nullable=True)
    old = database.Column(database.Integer)
    city=database.Column(database.String(100))
    user_id=database.Column(database.Integer, database.ForeignKey("users.id"))

    def __repr__(self):
        return f"users{self.id}"
with app.app_context():
    database.create_all()
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method=="POST":
        try:
            user=Users(email=request.form["email"], password=request.form["password"])
            database.session.add(user)
            database.session.flush()
            profile=Profiles(name=request.form["name"], old=request.form["old"], city=request.form["city"], user_id=user.id)
            database.session.add(profile)
            database.session.commit()
        except:
            database.session.rollback()
            print("Ошибка")
        
    
    return render_template("index.html")

@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        user = Users.query.filter_by(email=request.form['email']).first()
        if user and user.password == request.form['password']:
            return render_template('login.html', result='Вы вошли')
        else:
            return render_template('login.html', result='Вы не вошли')

    return render_template('login.html', result='Вы не вошли')


if __name__=="__main__":
    app.add_url_rule("/", "index", index)

    app.add_url_rule("/login", "login", login)
    app.run(debug=True)


