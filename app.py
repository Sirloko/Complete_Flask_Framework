from flask import Flask, render_template

app = Flask(__name__)

some_posts = [
    {
        'title': 'Post 1',
        'content': 'lorem ipsum',
        'author': 'enoch adeyemi'
    },
    {
        'title': 'Post 1',
        'content': 'dolor amet'
    }
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home/<int:id>')
def hello(id):
    return str(id) + " No 1"

@app.route('/posts')
def posts():
    return render_template('posts.html', posts=some_posts)



@app.route('/only', methods=['POST'])
def get_req():
    return 'Authorized 2'

if __name__ == "__main__":
    app.run(debug=True)