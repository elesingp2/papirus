from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ваш_секретный_ключ'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost:5432/mydatabase'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from sqlalchemy import Column, Integer, String, Boolean
 
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    profile_image = db.Column(db.String(120), nullable=True) 
    links = db.relationship('Link', backref='user', lazy=True)
    likes = db.relationship('Like', backref='user', lazy=True)
    has_viewed_profile = Column(Boolean, default=False)  

from datetime import datetime

class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(200), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True) 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    likes = db.relationship('Like', backref='link', lazy=True)
    dislikes = db.relationship('Dislike', backref='link', lazy=True)
    read_status = db.relationship('ReadStatus', backref='link', lazy=True)
    created_at = db.Column(db.DateTime, nullable=True, default=datetime.now())  

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    link_id = db.Column(db.Integer, db.ForeignKey('link.id'), nullable=False)

class Dislike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    link_id = db.Column(db.Integer, db.ForeignKey('link.id'), nullable=False)

class ReadStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    link_id = db.Column(db.Integer, db.ForeignKey('link.id'), nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    link_id = db.Column(db.Integer, db.ForeignKey('link.id'), nullable=False)
    user = db.relationship('User', backref='comments')
    link = db.relationship('Link', backref='comments')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите в систему для доступа к этой странице.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

from sqlalchemy import func

@app.route('/')
def index():
    # Получаем всех пользователей
    users = User.query.all()
    
    # Получаем количество лайков и прочтений за один запрос
    likes_counts = db.session.query(
        Like.user_id,
        func.count(Like.id).label('total_likes')
    ).join(Link).group_by(Like.user_id).all()

    reads_counts = db.session.query(
        ReadStatus.user_id,
        func.count(ReadStatus.id).label('total_reads')
    ).join(Link).group_by(ReadStatus.user_id).all()

    # Преобразуем результаты в словари
    user_likes = {user_id: total_likes for user_id, total_likes in likes_counts}
    user_reads = {user_id: total_reads for user_id, total_reads in reads_counts}

    today = datetime.utcnow().date()

    users = User.query.all()
    user_links_count = {}

    for user in users:
        # Считаем количество ссылок, добавленных сегодня
        count = Link.query.filter(
            Link.user_id == user.id,
            Link.created_at >= today
        ).count()
        
        if count > 0:
            user_links_count[user.id] = count  # Сохраняем только если больше 0

    return render_template('index.html', users=users, user_likes=user_likes, user_reads=user_reads, user_links_count=user_links_count)

@app.route('/user/<username>')
@login_required
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    
    # Получаем ссылки пользователя, отсортированные по времени (новые сверху)
    links = Link.query.filter_by(user_id=user.id).order_by(Link.created_at.desc()).all()
    reading_links = [link for link in links if link.read_status and any(rs.user_id == session['user_id'] for rs in link.read_status)]

    is_own_profile = (user.id == session['user_id'])
    
    today = datetime.utcnow().date() 
    
    return render_template('profile.html', user=user, links=links, is_own_profile=is_own_profile, reading_links=reading_links, today=today)

@app.route('/user/<username>/reading')
@login_required
def reading_links(username):
    user = User.query.filter_by(username=username).first_or_404()
    
    # Получаем ссылки, которые пользователь отметил как "читаю"
    reading_links = Link.query.filter(
        Link.user_id == user.id,
        Link.read_status.any(user_id=session['user_id'])
    ).order_by(Link.created_at.desc()).all()
    
    return render_template('reading_links.html', user=user, reading_links=reading_links)

from flask import request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        user.description = request.form['description'] 
        
        print(request.form['description'], 1111)
                # Обработка загрузки изображения
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join('static/profile_images', filename)
                file.save(file_path)  
                user.profile_image = file_path
                print(file_path, 0000)  

        db.session.commit()
        flash('Ок!')
        return redirect(url_for('user_profile', username=user.username))

    return render_template('edit_profile.html', user=user)

@app.route('/comment/<int:link_id>', methods=['POST'])
@login_required
def add_comment(link_id):
    link = Link.query.get_or_404(link_id)
    content = request.form['content']
    new_comment = Comment(content=content, user_id=session['user_id'], link_id=link_id)
    db.session.add(new_comment)
    db.session.commit()
    #flash('Добавлено')
    return redirect(url_for('user_profile', username=link.user.username))

@app.route('/delete_comment/<int:link_id>/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(link_id, comment_id):
    comment = Comment.query.get_or_404(comment_id)
    link = Link.query.get_or_404(link_id)
    if comment.user_id == session['user_id']:
        db.session.delete(comment)
        db.session.commit()
    return redirect(url_for('user_profile', username=link.user.username))

@app.route('/unlike/<int:link_id>', methods=['POST'])
@login_required
def unlike_link(link_id):
    link = Link.query.get_or_404(link_id)
    existing_like = Like.query.filter_by(user_id=session['user_id'], link_id=link_id).first()
    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()
    return redirect(url_for('user_profile', username=link.user.username))

@app.route('/read/<int:link_id>', methods=['POST'])
@login_required
def mark_as_read(link_id):
    link = Link.query.get_or_404(link_id)
    existing_read_status = ReadStatus.query.filter_by(user_id=session['user_id'], link_id=link_id).first()
    if not existing_read_status:
        new_read_status = ReadStatus(user_id=session['user_id'], link_id=link_id)
        db.session.add(new_read_status)
        db.session.commit()
    return redirect(url_for('user_profile', username=link.user.username))

@app.route('/unread/<int:link_id>', methods=['POST'])
@login_required
def mark_as_unread(link_id):
    link = Link.query.get_or_404(link_id)
    existing_read_status = ReadStatus.query.filter_by(user_id=session['user_id'], link_id=link_id).first()
    if existing_read_status:
        db.session.delete(existing_read_status)
        db.session.commit()
    return redirect(url_for('user_profile', username=link.user.username))

@app.route('/like/<int:link_id>', methods=['POST'])
@login_required
def like_link(link_id):
    link = Link.query.get_or_404(link_id)
    
    # Удаляем дизлайк, если он существует
    existing_dislike = Dislike.query.filter_by(user_id=session['user_id'], link_id=link_id).first()
    if existing_dislike:
        db.session.delete(existing_dislike)
    
    # Проверяем, поставил ли пользователь уже лайк на эту ссылку
    existing_like = Like.query.filter_by(user_id=session['user_id'], link_id=link_id).first()
    if not existing_like:
        new_like = Like(user_id=session['user_id'], link_id=link_id)
        db.session.add(new_like)
    
    db.session.commit()
    return redirect(url_for('user_profile', username=link.user.username))


@app.route('/dislike/<int:link_id>', methods=['POST'])
@login_required
def dislike_link(link_id):
    link = Link.query.get_or_404(link_id)
    
    # Удаляем лайк, если он существует
    existing_like = Like.query.filter_by(user_id=session['user_id'], link_id=link_id).first()
    if existing_like:
        db.session.delete(existing_like)
    
    # Проверяем, поставил ли пользователь уже дизлайк на эту ссылку
    existing_dislike = Dislike.query.filter_by(user_id=session['user_id'], link_id=link_id).first()
    if not existing_dislike:
        new_dislike = Dislike(user_id=session['user_id'], link_id=link_id)
        db.session.add(new_dislike)
    
    db.session.commit()
    return redirect(url_for('user_profile', username=link.user.username))

@app.route('/undislike/<int:link_id>', methods=['POST'])
@login_required
def undislike_link(link_id):
    link = Link.query.get_or_404(link_id)
    existing_dislike = Dislike.query.filter_by(user_id=session['user_id'], link_id=link_id).first()
    if existing_dislike:
        db.session.delete(existing_dislike)
        db.session.commit()
    return redirect(url_for('user_profile', username=link.user.username))

@app.route('/add_link', methods=['POST'])
@login_required
def add_link():
    url = request.form['url']
    title = request.form['title']
    description = request.form.get('description')  
    new_link = Link(
            title=title,
            url=url,
            user_id=session['user_id'],
            description=description,
            created_at=datetime.utcnow()  # Убедитесь, что это поле заполняется
        )
    db.session.add(new_link)
    db.session.commit()
    flash('Ты молодец!')
    return redirect(url_for('user_profile', username=session['username']))

@app.route('/delete_link/<int:link_id>', methods=['POST'])
@login_required
def delete_link(link_id):
    link = Link.query.get_or_404(link_id)
    if link.user_id == session['user_id']:
        db.session.delete(link)
        db.session.commit()
    return redirect(url_for('user_profile', username=session['username']))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Имя пользователя уже занято')
            return redirect(url_for('register'))
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Регистрация успешна. Теперь вы можете войти.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('user_profile', username=user.username))
        flash('Неверное имя пользователя или пароль')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)