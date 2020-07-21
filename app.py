from flask import Flask, render_template, request, redirect, flash, url_for, session, logging
from flask_mysqldb import MySQL
from wtforms import Form, FormField, TextAreaField, PasswordField, validators, StringField
from passlib.hash import sha256_crypt
import os
from functools import wraps
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'eportal4school'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['IMAGE_UPLOADS'] = 'static/img/uploads'
app.config['ALLOWED_IMAGE_EXTENSIONS'] = ["PNG", "JPG", "JPEG", "GIF"]
app.config['FLASK_ENV'] = 'development'
# app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024
app.config['MAX_IMAGE_FILESIZE'] = 0.5 * 1024 * 1024

def allowed_image(filename):
    if not "." in filename:
        return False
    ext = filename.rsplit(".", 1)[1]

    if ext.upper() in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return True
    else:
        return False



def allowed_image_filesize(filesize):

    if int(filesize) <= app.config['MAX_IMAGE_FILESIZE']:
        return True
    else:
        return False

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


#Edit Blogpost / Edit Article Route
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create cursor
    cur = mysql.connection.cursor()
    # Get article by ID
    result = cur.execute("SELECT * FROM blog WHERE id = %s", [id])
    article = cur.fetchone()

    #Get form
    form = ArticleForm(request.form)

    #Populate the fields
    form.title.data = article['title']
    form.content.data = article['content']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        content = request.form['content']
        #Create cursor
        cur = mysql.connection.cursor()
        #Execute
        cur.execute("UPDATE blog SET title=%s, content=%s WHERE id = %s", (title, content, id))
        #Commit to DB
        mysql.connection.commit()
        #Close connection
        cur.close()
        flash('Article Updated successfully', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_article.html', form=form)

#Delete Post / Detele article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    #Create cursor
    cur = mysql.connection.cursor()

    #Execute
    cur.execute("DELETE FROM blog WHERE id = %s", [id])
    #Commit to DB
    mysql.connection.commit()
    #Close connection
    cur.close()
    flash('Article Deleted successfully', 'success')
    return redirect(url_for('dashboard'))


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':

        if request.files:

            if not allowed_image_filesize(request.cookies.get("filesize")):
                flash('File exceeded MAX_IMAGE_FILESIZE', 'danger')
                return redirect(request.url)

            image = request.files["image"]
            if image.filename == ' ':
                flash('No selected file')

                return redirect(request.url)
            # check if the post request has the file part
            if not allowed_image(image.filename):
                flash('File type not allowed', 'danger')
                return redirect(request.url)

            else:
                filename = secure_filename(image.filename)

            image.save(os.path.join(app.config['IMAGE_UPLOADS'], filename))
            flash('Image upload success', 'success')

            return redirect(request.url)


    return render_template('upload.html')


if __name__ == "__main__":
    # app.secret_key = "hdhhf45555hhfh"
    app.secret_key = os.urandom(16)
    app.run(debug=True)