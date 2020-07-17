from flask import Flask, render_template, request, redirect, flash, url_for, session, logging
from flask_mysqldb import MySQL
from wtforms import Form, FormField, TextAreaField, PasswordField, validators, StringField
from passlib.hash import sha256_crypt
from datetime import datetime

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Initialize MYSQL
mysql = MySQL(app)


@app.route('/')
def index():
    return render_template('index.html')

class RegisterForm(Form):
    name = StringField(u'Name', validators=[validators.input_required(), validators.Length(min=1, max=50)])
    username  = StringField(u'Username', validators=[validators.input_required(), validators.Length(min=1, max=50)])
    email  = StringField(u'Email', validators=[validators.input_required(), validators.Length(min=6, max=50)])
    password  = PasswordField(u'Password', validators=[
        validators.Length(min=6, max=50),
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
        ])
    confirm  = PasswordField(u'Confirm Password')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        
        #Creating and executing Cursor
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password) )

        #Commiting the Database 
        mysql.connection.commit()

        #Closing the Cursor
        cur.close()

        flash('You are now registered, kindly login', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


# @app.route('/home/<int:id>')
# def hello(id):
#     return str(id) + " No 1"

@app.route('/posts', methods=['GET', 'POST'])
def posts():

    if request.method == 'POST':
        post_title = request.form['title']
        post_content = request.form['content']
        post_author = request.form['author']
        new_post = BlogPost(title = post_title, content = post_content, author=post_author)
        db.session.add(new_post)
        db.session.commit()
        return redirect('/posts')
    else:
        some_posts = BlogPost.query.order_by(BlogPost.date_posted).all()
        return render_template('posts.html', posts=some_posts)

@app.route('/posts/delete/<int:id>')
def delete(id):
    post = BlogPost.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    return redirect('/posts')

@app.route('/posts/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    post = BlogPost.query.get_or_404(id)
    if request.method == 'POST':
        
        post.title = request.form['title']
        post.content = request.form['content']
        post.author = request.form['author']
        
        db.session.commit()
        return redirect('/posts')
    else:
        return render_template('edit.html', post=post)

@app.route('/posts/new', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        
        post_title = request.form['title']
        post_content = request.form['content']
        post_author = request.form['author']
        new_post = BlogPost(title = post_title, content = post_content, author=post_author)
        db.session.add(new_post)
        db.session.commit()
        return redirect('/posts')
    else:
        return render_template('new_post.html')


# @app.route('/only', methods=['POST'])
# def get_req():
#     return 'Authorized 2'

if __name__ == "__main__":
    app.secret_key='secure456'
    app.run(debug=True)