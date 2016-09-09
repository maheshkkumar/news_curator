from app import app, lm
from flask import request, redirect, render_template, url_for, flash, g, current_app
from flask.ext.login import login_user, logout_user, login_required, current_user
from flask import Blueprint
from flask.ext.paginate import Pagination
from .forms import LoginForm, UploadForm, UserProfileForm, UserChangePassword
from .user import User
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo.errors import DuplicateKeyError, CursorNotFound, ExecutionTimeout, OperationFailure
from config import CATEGORIES
import datetime
import time
import validators
import re

mod = Blueprint('users', __name__)

# Finding the categories count
def article_categories():
    articles = app.config['ARTICLES_COLLECTION'].find()
    print "Articles = {}".format(articles.count())
    categories = {}
    for article in articles:
        # print article
        if article["category"] not in categories:
            categories[article["category"].encode("utf-8")] = 1
        else:
            categories[article["category"].encode("utf-8")] +=1
    return categories

# Dividing the articles dictionary into chunks
def chunks(l, n):
    n = max(1, n)
    return [l[i:i + n] for i in range(0, len(l), n)]

# Root Path
@app.route('/')
def home():
    return redirect(request.args.get("trending") or url_for("trending"))

# Implementation of a method to puluralize words based on count value given in the parameter
def pularize(count, word):
    if count < 2:
        return str(count) + ' ' + word + ' ago'
    else:
        return str(count) + ' ' + word +'s ' + 'ago'

# Method to get the CSS Framework
def get_css_framework():
    return current_app.config.get('CSS_FRAMEWORK', 'BOOTSTRAP3')

# Method to get the link sizes
def get_link_size():
    return current_app.config.get('LINK_SIZE', 'sm')

# Method to choose single page output or multi page output
def show_single_page_or_not():
    return current_app.config.get('SHOW_SINGLE_PAGE', False)

# Method to get the page items
def get_page_items():
    page = int(request.args.get('page', 1))
    per_page = request.args.get('per_page')
    if not per_page:
        per_page = current_app.config.get('PER_PAGE', 20)
    else:
        per_page = int(per_page)
    offset = (page - 1) * per_page
    return page, per_page, offset

# Method to define pagination for the pages with more than 20 items
def get_pagination(**kwargs):
    kwargs.setdefault('article_name', 'articles')
    return Pagination(css_framework=get_css_framework(),
                        link_size=get_link_size(),
                        show_single_page=show_single_page_or_not(),
                        **kwargs)
        
# Method for User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            user = app.config['USERS_COLLECTION'].find_one({"_id": form.username.data})
            if user and User.validate_login(user['password'], form.password.data):
                user_obj = User(user['_id'])
                login_user(user_obj)
                flash("Welcome {}!".format(user['_id']), category='success')
                return redirect(request.args.get("trending") or url_for("trending"))
            else:
                flash("Invalid Password", category='error')
                return render_template('login.html', title='login', form=form)
        else:
            flash("Username or Password is empty!", category='error')
            return render_template('login.html', title='login', form=form)
    else:
        return render_template('login.html', title='login', form=form)

# Method for User Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = LoginForm()
    if request.method == 'POST':
        if form.username.data:
            try:
                password_hash = generate_password_hash(form.password.data, method='pbkdf2:sha256')
                user_data = {
                    "_id": form.username.data, 
                    "password": password_hash, 
                    "user_score": 0  
                }
                bool_insert = app.config['USERS_COLLECTION'].insert(user_data)
                if bool_insert:
                    flash("Signup successfully!", category='success')
                    return redirect(request.args.get("login") or url_for("login"))
                else:
                    flash("Signup failed. Try again.", category='error')
                    return render_template('login.html', title='login', form=form)
            except:
                flash("Username already exists in our community!", category='error')
                return render_template('login.html', title='login', form=form)
        
        flash("Username is empty", category='error')
        return render_template('signup.html', title='signup', form=form)
   
    else:
        return render_template('signup.html', title='signup', form=form)


# Method to Submit a latest news article
@app.route('/submit_article', methods=['POST', 'GET'])
def submit_article():
    if current_user.is_authenticated():
        form = UploadForm()
        if request.method == 'POST' and form.validate_on_submit():
            if validators.url(form.link.data):
                ts = time.time()
                data = {
                    "_id": form.link.data,
                    "description": form.description.data,
                    "category": form.category.data,
                    "user": current_user.username,
                    "createdAt":  datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                }

                try:
                    current_score = app.config['USERS_COLLECTION'].find_one({"_id": current_user.username})
                    if((app.config['NEWS_COLLECTION'].insert(data)) and app.config['USERS_COLLECTION'].update({"_id": current_user.username}, 
                                                                        {"$set": {"user_score": int(current_score["user_score"])+1}})):
                        flash("Link added successfully", category="success")
                        return redirect(request.args.get("latest") or url_for("latest"))

                except DuplicateKeyError:
                    flash("Article link already exists in the Database", category="error")
                    return render_template("submit_article.html", form=form)
            else:
                flash("Not a valid link", category="error")
                return render_template("submit_article.html", form=form)

        return render_template('submit_article.html', title='Submit Article', form=form)
    else:
        flash("Login to submit a link", category="error")
        return redirect(request.args.get("login") or url_for("login"))

# List of all the categories
@app.route('/category')
def total_categories():
    categories_chunks = chunks(CATEGORIES, 3)
    categories_count = article_categories()
    return render_template('total_categories.html', categories_chunks=categories_chunks, categories=CATEGORIES, categories_count=categories_count)

# Details of a specific category
@app.route('/category/<string:category_type>')
def category_selection(category_type):
    article_category = [item[0] for item in CATEGORIES if item[1] == category_type]
    if len(article_category) > 0:
        total = app.config['ARTICLES_COLLECTION'].find({"category": article_category[0]}).count()
        page, per_page, offset = get_page_items()
        try:
            sort = [("createdAt", -1)]
            query_result = app.config['ARTICLES_COLLECTION'].find({"category": article_category[0]}).sort(sort)
            articles = query_result.skip(offset).limit(per_page)
            articles_length = articles.count() if articles else 0
            pagination = get_pagination(page=page, per_page=per_page, total=total, 
                                    record_name=articles)
            return render_template('category.html', articles=articles, page=page,
                            per_page=per_page, pagination=pagination, category_type=category_type, articles_length=articles_length)
        except ValueError:        
            total = 0
            return render_template('category.html', total=total)
    else:
         return render_template('404.html'), 404

# 404 Page
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Method for User to Logout
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# Method for Latest News/Recent News
@app.route('/latest', methods=['GET'])
def latest():
    total = app.config['NEWS_COLLECTION'].find().count()
    page, per_page, offset = get_page_items()
    try:
        sort = [("createdAt", -1)]
        query_result = app.config['NEWS_COLLECTION'].find().sort(sort)
        articles = query_result.skip(offset).limit(per_page)
        articles_length = articles.count() if articles else 0
        pagination = get_pagination(page=page, per_page=per_page, total=total, 
                                record_name=articles)
        return render_template('latest.html', articles=articles, page=page,
                            per_page=per_page, pagination=pagination, articles_length=articles_length)
    except ValueError:        
        total = 0
        return render_template('latest.html', total=total)

# Top Stories or top trending stories
@app.route('/trending', methods=['GET'])
def trending():
    total = app.config['ARTICLES_COLLECTION'].find().count()
    page, per_page, offset = get_page_items()
    try:
        sort = [("createdAt", -1)]
        query_result = app.config['ARTICLES_COLLECTION'].find().sort(sort)
        articles = query_result.skip(offset).limit(per_page)
        articles_length = articles.count() if articles else 0
        pagination = get_pagination(page=page, per_page=per_page, total=total, 
                                record_name=articles)
        return render_template('trending.html', articles=articles, page=page,
                                per_page=per_page, pagination=pagination, articles_length=articles_length)
    except ValueError:        
        total = 0
        return render_template('trending.html', total=total)

# User profile 
@app.route('/profile', methods=['POST', 'GET'])
def profile():
    login_required
    form = UserProfileForm(request.form)
    user = app.config['USERS_COLLECTION'].find_one({"_id": current_user.username})
    try:
        if request.method == 'POST' and form.validate_on_submit:
            if form.email.data:
                user_data = app.config['USERS_COLLECTION'].find_one({"_id": current_user.username})
                match = re.search(r'[\w.-]+@[\w.-]+.\w+', form.email.data)
                if match:
                    bool_insert = app.config['USERS_COLLECTION'].update({ "_id": current_user.username },{ "$set": {"email": form.email.data }})     
                    if bool_insert:
                        flash("Email was updated!", category='success')
                        return redirect(request.args.get("profile") or url_for("profile"))                       
                    else:    
                        flash("Email was not updated!", category='error')
                        return render_template('profile.html', user=user, form=form)
                else:
                    flash("Incorrect email!", category='error')
                    return render_template('profile.html', user=user, form=form)
            else:
                flash("Please, provide an email address", category='error')
                return render_template('profile.html', user=user, form=form)
        else:
            user = app.config['USERS_COLLECTION'].find_one({"_id": current_user.username})
            return render_template('profile.html', user=user, form=form)
    
    except CursorNotFound:
        flash("Unfortunately, something unexpected occured.", category='error')
        return render_template('profile.html', user=user, form=form)
    except ExecutionTimeout:
        flash("Unfortunately, something unexpected occured while executing.", category='error')
        return render_template('profile.html', user=user, form=form)
    except OperationFailure:
        flash("Unfortunately, your operation failed, try doing it again", category='error')    
        return render_template('profile.html', user=user, form=form)

# Change Password for the users
@app.route('/change_password', methods=['POST', 'GET'])
def change_password():
    login_required
    form = UserChangePassword(request.form)
    user = app.config['USERS_COLLECTION'].find_one({"_id": current_user.username})
    try:
        if request.method == 'POST' and form.validate_on_submit:
            if form.current_password.data:
                user_data = app.config['USERS_COLLECTION'].find_one({"_id": current_user.username})
                if (form.current_password.data != form.password.data):
                    if (check_password_hash(user_data["password"], form.current_password.data)):
                        password_hash = generate_password_hash(form.password.data, method='pbkdf2:sha256')
                        bool_insert = app.config['USERS_COLLECTION'].update({"_id": current_user.username}, { "$set": {"password": password_hash}})     
                        if bool_insert:
                            flash("Password was changed successfully!", category='success')
                            return redirect(request.args.get("trending") or url_for("trending"))                       
                        else:    
                            flash("Password was not changed!", category='error')
                            return render_template('change_password.html', user=user, form=form)
                    else:
                        flash("Current Password is incorrent!", category='error')
                        return render_template('change_password.html', user=user, form=form)
                else:
                    flash("Please, provide a differnt password this time!", category='error')
                    return render_template('change_password.html', user=user, form=form)
            else:
                flash("Password is empty!", category='error')
                return render_template('change_password.html', user=user, form=form)
        else:
            user = app.config['USERS_COLLECTION'].find_one({"_id": current_user.username})
            return render_template('change_password.html', user=user, form=form)
    
    except CursorNotFound:
        flash("Unfortunately, something unexpected occured.", category='error')
    except KeyError:
        flash("Unfortunately, something unexpected occured.", category='error')
        return render_template('profile.html', user=user, form=form)
    except ExecutionTimeout:
        flash("Unfortunately, something unexpected occured while executing.", category='error')
        return render_template('profile.html', user=user, form=form)
    except OperationFailure:
        flash("Unfortunately, your operation failed, try doing it again", category='error')    
        return render_template('profile.html', user=user, form=form)


# Flask filter method which can be called from the Jinja template
# template_file to format the time for the articles
@app.template_filter()
def datetimeformat(datetimeformat):
    date_format = "%Y-%m-%d %H:%M:%S"
    time_now = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    end_date = datetime.datetime.strptime(time_now, date_format)
    start_date = datetime.datetime.strptime(datetimeformat, date_format)
    days = abs((end_date - start_date).days)
    hours = abs((end_date - start_date).seconds) / 3600
    minutes = abs((end_date - start_date).seconds) / 60
    seconds = abs((end_date - start_date).seconds)
    if days > 0:
        if days >= 365:
            return str(pularize(days/365, 'year'))
        elif days > 30 and days < 365:
            return str(pularize(days/30, 'year'))
        else:
            return str(pularize(days, 'day'))
    elif hours > 0:
        return str(pularize(hours, "hour"))
    else:
        if minutes > 0:
            return str(pularize(minutes, "minute"))
        else:
            return str(pularize(seconds, "second"))

# template_filter (user_length_modifier) -> It is used to calculate the length of username
# If the username length > 10, we modify it accordingly
@app.template_filter()
def username_length_modifier(username):
    if len(username) > 10:
        username = str(username[:9])+".."
        return username
    else:
        return username  

# template_filter to find the article category, where the catgory is a tuple
@app.template_filter()
def find_article_category(article_type):
    category =  [item for item in CATEGORIES if item[0] == article_type]
    return category

# Method to load users credentials
@lm.user_loader
def load_user(username):
    u = app.config['USERS_COLLECTION'].find_one({"_id": username})
    if not u:
        return None
    return User(u['_id'])
