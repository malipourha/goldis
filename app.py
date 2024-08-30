from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from functools import wraps

# بعد از تعریف app و db


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)  

    def __repr__(self):
        return f'<User {self.username}>'

from datetime import datetime

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    body = db.Column(db.Text, nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    published = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Post {self.title}>'


class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    state = db.Column(db.String(20), default='active')  
    posts = db.relationship('Post', backref='topic', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

with app.app_context():
    
    db.create_all()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash('You need to be logged in to access this page.', 'warning')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(email=session['user_email']).first()
        if user.role != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('home'))  
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if 'username' in request.form:  
            username = request.form['username']
            email = request.form['email']
            password = request.form['pswd']
            
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('Email already exists.')
            else:
                user = User(username=username, email=email, password=password, role='user')  
                db.session.add(user)
                db.session.commit()
                flash(f'Account created successfully for {username}!')
        else:  # Login
            email = request.form['email']
            password = request.form['pswd']
            
            user = User.query.filter_by(email=email).first()
            if user and user.password == password:
                session['user_email'] = email
                flash('Logged in successfully!')
                return redirect(url_for('home'))
            else:
                flash('Invalid email or password.')
        
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/menu')
def menu():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(email=session['user_email']).first()
    
    return render_template('menu.html', username=user.username)


@app.route('/home')
def home():
    posts = Post.query.filter_by(published=True).limit(4).all()
    topics = Topic.query.all()
    users = User.query.all()
    return render_template('home.html', posts=posts, topics=topics, users=users)


@app.route('/blogs')
def blogs():
    topic = request.args.get('topic', None)  
    if topic:
        selected_topic = Topic.query.filter_by(name=topic).first()
    else:
        selected_topic = None
    
    return render_template('blogs.html', topic=selected_topic)

@app.route('/test/<int:user_id>')
def test(user_id):
    return f"Test route for user {user_id}"

@app.route('/blogs2/<int:user_id>')
def blogs2(user_id):
    user = User.query.get_or_404(user_id)
    posts = Post.query.filter_by(user_id=user.id, published=True).all()
    post_count = len(posts)
    return render_template('blogs2.html', user=user, posts=posts, post_count=post_count)


@app.route('/blogs3/<string:topic_name>')
def blogs3(topic_name):
    topic = Topic.query.filter_by(name=topic_name).first_or_404()
    posts = Post.query.filter_by(topic_id=topic.id, published=True).all()
    return render_template('blogs3.html', topic=topic, posts=posts)

@app.route('/about', methods=['GET', 'POST'])
def about():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        new_comment = Comment(name=name, email=email, message=message)
        db.session.add(new_comment)
        db.session.commit()
        flash('Comment submitted successfully!')
        return redirect(url_for('about'))

    comments = Comment.query.order_by(Comment.date.desc()).all()
    return render_template('single.html', comments=comments)

@app.route('/contact')
def contact():
    return render_template('comingsoon.html')

@app.route('/single', methods=['GET', 'POST'])
def single():
    topics = Topic.query.all()
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        new_comment = Comment(name=name, email=email, message=message)
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('single'))

    comments = Comment.query.order_by(Comment.date.desc()).all()
    return render_template('single.html', comments=comments, topics=topics)


@app.route('/dashboard')
def dashboard():
    
    if 'user_email' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/admin/posts')
def admin_posts():
    posts = Post.query.all()
    return render_template('admin/posts/index.html', posts=posts)

@app.route('/admin/users')
@admin_required
def admin_users():
    if 'user_email' not in session:
        return redirect(url_for('login'))

    users = User.query.all()  
    return render_template('admin/users/index.html', users=users)


@app.route('/admin/topics')
@admin_required
def admin_topics():
    topics = Topic.query.all() 
    return render_template('admin/topics/index.html', topics=topics)

@app.route('/topic/<topic>')
def topic(topic):
      return render_template('bolgs.html', topic=topic)

@app.route('/admin/posts/create', methods=['GET', 'POST'])
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        topic_name = request.form['topic']
        
        topic = Topic.query.filter_by(name=topic_name).first()
        user = User.query.filter_by(email=session['user_email']).first()
        
        if topic and user:
            post = Post(title=title, body=body, topic_id=topic.id, user_id=user.id)
            db.session.add(post)
            db.session.commit()
        if not topic:
            return redirect(url_for('create_post'))

        if not user:
            return redirect(url_for('create_post'))

        return redirect(url_for('admin_posts'))
    topics = Topic.query.all()
    return render_template('admin/posts/create.html', topics= topics)

@app.route('/admin/posts/edit/<int:id>', methods=['GET', 'POST'])
def edit_post(id):
    post = Post.query.get_or_404(id)
    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        db.session.commit()
        return redirect(url_for('admin_posts'))
    return render_template('create_post.html', post=post)

@app.route('/admin/posts/delete/<int:id>', methods=['POST'])
def delete_post(id):
    post = Post.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully')
    return redirect(url_for('admin_posts'))

@app.route('/admin/posts/publish/<int:id>', methods=['GET', 'POST'])
def publish_post(id):
    post = Post.query.get_or_404(id)
    post.published = not post.published
    db.session.commit()
    flash('Post status updated successfully')
    return redirect(url_for('admin_posts'))

@app.route('/admin/topics/create', methods=['GET', 'POST'])
@admin_required
def create_topic():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        
        existing_topic = Topic.query.filter_by(name=name).first()
        if existing_topic:
            flash('Topic with this name already exists')
            return redirect(url_for('create_topic'))
        
        topic = Topic(name=name, description=description)
        db.session.add(topic)
        db.session.commit()
        
        
        return redirect(url_for('admin_topics'))
    
    return render_template('admin/topics/create.html')


@app.route('/admin/topics/edit/<int:id>', methods=['GET', 'POST'])
def edit_topic(id):
    topic = Topic.query.get_or_404(id)
    if request.method == 'POST':
        topic.name = request.form['name']
        topic.description = request.form['description']
        topic.state = request.form['state']
        db.session.commit()
        flash('Topic updated successfully')
        return redirect(url_for('admin_topics'))
    return render_template('admin/topics/create.html', topic=topic)

@app.route('/admin/topics/delete/<int:id>', methods=['POST'])
def delete_topic(id):
    topic = Topic.query.get_or_404(id)
    db.session.delete(topic)
    db.session.commit()
    flash('Topic deleted successfully')
    return redirect(url_for('admin_topics'))

@app.route('/admin/users/create', methods=['GET', 'POST'])
@admin_required
def create_user():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirmation = request.form.get('password_confirmation')
        role = request.form.get('role')
        
        #if password != password_confirmation:
         #   return "Passwords do not match", 400
        
        user = User(username=username, email=email, password=password, role=role)
        db.session.add(user)
        db.session.commit()
        
        return redirect(url_for('admin_users'))
    return render_template('admin/users/create.html')

@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        user.role = request.form['role']
        db.session.commit()
        flash('User updated successfully')
        return redirect(url_for('admin_users'))

    return render_template('admin/users/create.html', user=user)

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully')
    return redirect(url_for('admin_users'))


# Logout route
@app.route('/logout')
def logout():
    session.pop('user_email', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run()
