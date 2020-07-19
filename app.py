from flask import Flask, render_template, request, redirect, flash, url_for, session, logging
from flask_mysqldb import MySQL
from wtforms import Form, FormField, TextAreaField, PasswordField, validators, StringField
from passlib.hash import sha256_crypt
from datetime import datetime
from functools import wraps

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'eportal4school'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Initialize MYSQL
mysql = MySQL(app)


@app.route('/')
def index():
    return render_template('index.html')

#Register Form Class
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

#User Registration Route
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

#User Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method =='POST':
        #get form fields
        username = request.form['username']
        password_c = request.form['password']

        #create cursor
        cur = mysql.connection.cursor()

        #get user by username

        result = cur.execute("SELECT * FROM users WHERE username = %s ", [username])

        if result > 0:
            #get stored hash
            data = cur.fetchone()
            password = data['password']

            #compare passwords
            if sha256_crypt.verify(password_c, password):
                #Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))

            else:
                error = 'Invalid Login'
                return render_template('login.html', error=error)
                #close connection
            cur.close()
        else:
            error = 'Username Not found'
            return render_template('login.html', error=error)
    return render_template('login.html')


#Check if User is Logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please Login', 'danger')
            return redirect(url_for('login'))
    return wrap

#Logout Route
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

#Dashboard Route
@app.route('/dashboard')
@is_logged_in
def dashboard():
    #Create Cursor
    cur = mysql.connection.cursor()
    #Get Articles
    result = cur.execute("SELECT * FROM blog")
    articles = cur.fetchall()
    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No Articles found'
        return render_template('dashboard.html', msg=msg)
    #Close Connection
    cur.close()

#Blog / Article Route
@app.route('/blog')
def blog():
    #Create Cursor
    cur = mysql.connection.cursor()
    #Get Articles
    result = cur.execute("SELECT * FROM blog")
    articles = cur.fetchall()
    if result > 0:
        return render_template('blog.html', articles=articles)
    else:
        msg = 'No Articles found'
        return render_template('blog.html', msg=msg)
    #Close Connection
    cur.close()

#BlogPosts / Single Article Route
@app.route('/article/<string:id>')
def article(id):
    #Create Cursor
    cur = mysql.connection.cursor()
    #Get Article
    result = cur.execute("SELECT * FROM blog WHERE id = %s", [id])
    article = cur.fetchone()
    return render_template('article.html', article=article)

#Blogpost / Article class
class ArticleForm(Form):
    title = StringField(u'Title', validators=[validators.input_required(), validators.Length(min=1, max=200)])
    # author = StringField(u'Author', validators=[validators.Length(min=1, max=100)])
    content  = TextAreaField(u'Content', validators=[validators.input_required(), validators.Length(min=30)])
    
#New Blogpost / add Article Route
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        content = form.content.data
        #Create cursor
        cur = mysql.connection.cursor()
        #Execute
        cur.execute("INSERT INTO blog (title, author, content) VALUES(%s, %s, %s)", (title, session['username'], content))
        #Commit to DB
        mysql.connection.commit()
        #Close connection
        cur.close()
        flash('Article created successfully', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html', form=form)








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