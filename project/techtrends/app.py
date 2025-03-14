import sqlite3
import logging
import sys

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

db_connection_count = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row

    global db_connection_count
    db_connection_count += 1

    return connection

# Function to get number of posts in DB
def get_no_posts():
    connection = get_db_connection()
    no_posts = connection.execute('SELECT COUNT(DISTINCT ID) FROM posts',
                        ).fetchone()
    connection.close()
    return int(no_posts[0])

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

@app.route('/healthz')
def healthz():
    response = app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=200,
            mimetype='application/json'
    )

    return response

@app.route('/metrics')
def metrics():
    response = app.response_class(
            response=json.dumps({"db_connection_count": db_connection_count, "post_count": get_no_posts()}),
            status=200,
            mimetype='application/json'
    )

    return response

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.warning('Article with id "{}" does not exist'.format(post_id))
        return render_template('404.html'), 404      
    else:
      app.logger.info('Article "{}" retrieved'.format(post['title']))
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('About Us page retrieved')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()            
            connection.close()

            app.logger.info('Article "{}" created'.format(title))

            return redirect(url_for('index'))

    return render_template('create.html')

def setup_logging():
    # Set up logging
    # format =%(asctime)s - %(message)s  
    log_format = '%(levelname)s:%(name)s:%(asctime)s, %(message)s'
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format=log_format)
    # Send logs to syserr
    syserr_handler = logging.StreamHandler(sys.stdout)
    syserr_handler.setFormatter(logging.Formatter(log_format))
    syserr_handler.setLevel(logging.WARNING)
    logging.getLogger().addHandler(syserr_handler)    

# start the application on port 3111
if __name__ == "__main__":
   
   #set up logging
   setup_logging()
   
   
   app.run(host='0.0.0.0', port='3111')
