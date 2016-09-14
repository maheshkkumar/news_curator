from app import app, lm
from flask import request, redirect, render_template, url_for, flash, current_app
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
from dependency import pularize

# Root Path
@app.route('/')
def home():
    return redirect(request.args.get("trending") or url_for("trending"))
        
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
                    "user_score": 0, 
                    "likes": [],
                    "recommend": []   
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

# 404 Page
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Method for User to Logout
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

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
