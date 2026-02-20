from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
import json
import os
import math
from flask_mail import Mail, Message
from datetime import datetime
from werkzeug.utils import secure_filename

local_server = True
#thse line of code is Actually for Json file and its parameters
with open("config.json", "r") as  config_file:
    config = json.load(config_file)
    params = config["params"]
    params_html = config["params_html"]
    email_params = config["email_params"]
    about_params = config["about_params"]
    login_params = config["login_params"]
    uploder_param = config["uploder_param"]

  #  params =json.load(config_file)["params"],
   # params_html =json.load(config_file)["params_html"]
app = Flask(__name__)
app.secret_key ='Super-Secret-key'
app.config['UPLOAD_FOLDER'] = uploder_param['uplode_location']

# --- Mail Configuration ---
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME=email_params['gmail_user'],
    MAIL_PASSWORD=email_params['gmail_password']
)
mail = Mail(app)

#here we are taking local server and production server in "if-else" condition and we are using SQLAlchemy
#to connect to these mysql server
if (local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI']= params['prod_uri']

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#these line code for the database connection of Contact Form so here we created the
# Class by the name of that Table name in the Database which is "Contact"
class Contact(db.Model):
    """Serial_no, Name, Email, Phone_num, Message, date"""
    Serial_no = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(50), nullable=False)
    Email = db.Column(db.String(20), nullable=False)
    Phone_num = db.Column(db.String(13),  nullable=False)
    Message = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=True)


#these line code for the database connection of 'first post' Form so here we created the
# Class by the name of that Table name in the Database which is "post"
class Posts(db.Model):
    """Serial_no, title, sub_title, slug, Content, img_file, date, post_by"""
    serial_no = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    sub_title = db.Column(db.String(20), nullable=False)
    slug = db.Column(db.String(13),  nullable=False)
    content = db.Column(db.Text, nullable=False)
    img_file = db.Column(db.String(15), nullable=False)
    post_by = db.Column(db.String(13),  nullable=False)
    date = db.Column(db.DateTime, nullable=True)

#this Route or Endpoint is for Dashboard page where we fetch all the Blogs
@app.route('/dashboard', methods=['GET', 'POST'])
def deshboard():
    merged_config = {**params_html, **login_params}
    if ('admin' in session and session['admin'] == login_params['admin_username']):
        post = Posts.query.all()
        return render_template('dashboard.html', config=merged_config, posts=post)

    if request.method == 'POST':
        username = request.form.get('username')
        userpass = request.form.get('pass')
        if (username == login_params['admin_username'] and userpass == login_params['admin_password']):
            session ['admin'] = username
            post = Posts.query.all()
            return render_template('dashboard.html', config=merged_config, posts=post )

    return render_template('login.html', config=merged_config)

#this Route is for Adding new blog and can Edit old Blog
@app.route('/edit/<string:serial_no>', methods=['GET', 'POST'])
def edit(serial_no):
    if ('admin' in session and session['admin'] == login_params['admin_username']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            box_sub_title = request.form.get('sub_title')
            box_slug = request.form.get('slug')
            box_content = request.form.get('content')
            box_image_file = request.form.get('img_file')
            box_post_by = request.form.get('post_by')
            date = datetime.now()
            if serial_no == '0':
                post = Posts (title = box_title, sub_title = box_sub_title, slug=box_slug, content=box_content, img_file=box_image_file, post_by=box_post_by, date=date )
                db.session.add(post)
                db.session.commit()
                return redirect('/edit/'+ serial_no)

            else:
                post = Posts.query.filter_by(serial_no=serial_no).first()
                post.title = box_title
                post.sub_title = box_sub_title
                post.slug = box_slug
                post.content = box_content
                post.img_file = box_image_file
                post.post_by = box_post_by
                post.date = date
                db.session.commit()
                return redirect('/edit/'+ serial_no)

    post = Posts.query.filter_by(serial_no=serial_no).first()
    return render_template("edit.html", config=params_html, post=post)


#here this endpoint or Route is For Uploder
@app.route('/uploader', methods=['GET', 'POST'])
def uploader():
    if ('admin' in session and session['admin'] == login_params['admin_username']):
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Files uploaded Successfully"

#this Route or Endpoint is for logout
@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/dashboard')

#this Endpoint or route is for Deleting blog
@app.route('/delete/<string:serial_no>', methods=['GET', 'POST'])
def delete(serial_no):
    if ('admin' in session and session['admin'] == login_params['admin_username']):
        post = Posts.query.filter_by(serial_no=serial_no).first()
        db.session.delete(post)
        db.session.commit()
        return redirect('/dashboard')


#the App.route function for Home page of web app
@app.route('/')
def index():
    # Get page number
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)

    # Pagination setup
    no_of_posts = int(params_html['no_of_posts'])
    offset = (page - 1) * no_of_posts

    # Get current page posts
    posts = Posts.query.offset(offset).limit(no_of_posts).all()

    # Compute last page from total posts
    total_posts = Posts.query.count()
    last_page = math.ceil(total_posts / no_of_posts)

    # Pagination links
    if page == 1:
        prev = "#"
        next = "/?page=" + str(page + 1)
    elif page == last_page:
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)

    return render_template('index.html', config=params_html, posts=posts, prev=prev, next=next)


#the App.route function for about page of web app
@app.route("/about")
def about():
    return render_template('about.html', about=about_params, config=params_html)

#the App.route function for Contact page of web page
@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        #here we get the entry request which comes from the user
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        entry = Contact(Name=name, Email=email, Phone_num=phone, Message=message, date=datetime.now())
        db.session.add(entry)
        db.session.commit()

        #it is the message porstion  here we recive the user message in email using contact Form
        # Send email notification
        msg = Message(
            subject=f"New Message from {name}",
            sender=email,
            recipients=[email_params['gmail_user']],
            body=f"Message: {message}\nPhone: {phone}\nEmail: {email}"
        )
        mail.send(msg)
        return render_template("contact.html", config=params_html)

    return render_template("contact.html", config=params_html)  # Response after POST


#the App.route function for Post page of web app
@app.route("/post/<string:slug_post>", methods=['GET'])
def post_route(slug_post):
    post = Posts.query.filter_by(slug=slug_post).first()
    return render_template("post.html", config=params_html, post=post)


if __name__ == '__main__':
    # It's a good practice to put app.run inside an if block

    # --- FIX: Database Table Creation ---
    # This block ensures the tables defined by your models (like Contact)
    # are created in the database when the application starts if they don't exist.
    with app.app_context():
        db.create_all()

app.run(debug=True)