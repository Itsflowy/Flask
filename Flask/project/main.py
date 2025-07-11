from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Папка для загрузки файлов заданий
database = SQLAlchemy(app)

# Создаем папку для загрузок, если ее нет
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class Users(database.Model):
    id = database.Column(database.Integer, primary_key=True) 
    email = database.Column(database.String(100), unique=True)
    password = database.Column(database.String(50), nullable=True)
    data = database.Column(database.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"users{self.id}"

class Profiles(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(50), nullable=True)
    old = database.Column(database.Integer)
    city = database.Column(database.String(100))
    user_id = database.Column(database.Integer, database.ForeignKey("users.id"))

    def __repr__(self):
        return f"profiles{self.id}"

class Tasks(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    title = database.Column(database.String(100), nullable=False)
    description = database.Column(database.Text)
    file_path = database.Column(database.String(200))  # Путь к загруженному файлу
    created_at = database.Column(database.DateTime, default=datetime.utcnow)
    user_id = database.Column(database.Integer, database.ForeignKey("users.id"))
    is_completed = database.Column(database.Boolean, default=False)

    def __repr__(self):
        return f"tasks{self.id}"

with app.app_context():
    database.create_all()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            # Создаем пользователя
            user = Users(email=request.form["email"], password=request.form["password"])
            database.session.add(user)
            database.session.flush()
            
            # Создаем профиль
            profile = Profiles(
                name=request.form["name"],
                old=request.form["old"],
                city=request.form["city"],
                user_id=user.id
            )
            database.session.add(profile)
            database.session.commit()
            
            # Авторизуем пользователя
            session['user_id'] = user.id
            return redirect(url_for('mainpage'))
            
        except Exception as e:
            database.session.rollback()
            print(f"Ошибка: {e}")
            flash('Ошибка регистрации. Возможно, email уже занят.')
    
    return render_template("index.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = Users.query.filter_by(email=request.form['email']).first()
        if user and user.password == request.form['password']:
            session['user_id'] = user.id
            return redirect(url_for('mainpage'))
        else:
            flash('Неверный email или пароль')
    
    return render_template('login.html')

@app.route('/mainpage', methods=['GET', 'POST'])
def mainpage():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    profile = Profiles.query.filter_by(user_id=user_id).first()
    
    # Обработка загрузки нового задания
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        file = request.files.get('file')
        
        if title:
            file_path = None
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                file_path = f"uploads/{filename}"  # Сохраняем относительный путь
            
            new_task = Tasks(
                title=title,
                description=description,
                file_path=file_path,
                user_id=user_id
            )
            database.session.add(new_task)
            database.session.commit()
            flash('Задание успешно добавлено!')
    
    # Получаем все задания (кроме выполненных)
    tasks = Tasks.query.filter_by(is_completed=False).order_by(Tasks.created_at.desc()).all()
    
    return render_template('mainpage.html', profile=profile, tasks=tasks)

@app.route('/complete_task/<int:task_id>')
def complete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    task = Tasks.query.get_or_404(task_id)
    task.is_completed = True
    database.session.commit()
    flash('Задание отмечено как выполненное!')
    return redirect(url_for('mainpage'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)