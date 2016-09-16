from app import app, lm
from flask import request, redirect, render_template, url_for, flash
from flask.ext.login import current_user
from flask.ext.paginate import Pagination
from .forms import UploadForm
from .user import User
from pymongo.errors import DuplicateKeyError, CursorNotFound, ExecutionTimeout, OperationFailure
from config import CATEGORIES
import datetime
import time
import validators
from dependency import get_pagination, chunks, article_categories
from dependency import get_count, articles_stat, get_articles
import json

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
        collection = 'ARTICLES_COLLECTION'
        condition_key = "category" 
        condition_value = article_category[0]
        try:
            articles, articles_length, page, per_page, offset = get_articles(collection, condition_key, condition_value)
            pagination = get_pagination(page=page, per_page=per_page, total=total, 
                                    record_name=articles)
            if current_user.is_authenticated():
                likes = app.config['USERS_COLLECTION'].find_one({"_id": current_user.username})["likes"]
                return render_template('trending.html', articles=articles, page=page,
                                per_page=per_page, pagination=pagination, articles_length=articles_length, likes=likes)
            else:
                return render_template('trending.html', articles=articles, page=page,
                                per_page=per_page, pagination=pagination, articles_length=articles_length)
        except ValueError:        
            total = 0
            return render_template('category.html', total=total)
    else:
         return render_template('404.html'), 404

# Method for Latest News/Recent News
@app.route('/latest', methods=['GET'])
def latest():
    collection = 'NEWS_COLLECTION'
    try:
        total = get_count(collection)
        articles, articles_length, page, per_page, offset = articles_stat(collection)
        pagination = get_pagination(page=page, per_page=per_page, total=total, 
                                record_name=articles)
        if current_user.is_authenticated():
            likes = app.config['USERS_COLLECTION'].find_one({"_id": current_user.username})["likes"]
            return render_template('trending.html', articles=articles, page=page,
                                per_page=per_page, pagination=pagination, articles_length=articles_length, likes=likes)
        else:
            return render_template('trending.html', articles=articles, page=page,
                                per_page=per_page, pagination=pagination, articles_length=articles_length)
    except ValueError:        
        total = 0
        return render_template('trending.html', total=total)
    except ValueError:        
        total = 0
        return render_template('latest.html', total=total)

# Top Stories or top trending stories
@app.route('/trending', methods=['GET'])
def trending():
    collection = 'ARTICLES_COLLECTION'
    try:
        total = get_count(collection)
        articles, articles_length, page, per_page, offset = articles_stat(collection)
        pagination = get_pagination(page=page, per_page=per_page, total=total, 
                                record_name=articles)
        if current_user.is_authenticated():
            likes = app.config['USERS_COLLECTION'].find_one({"_id": current_user.username})["likes"]
            return render_template('trending.html', articles=articles, page=page,
                                per_page=per_page, pagination=pagination, articles_length=articles_length, likes=likes)
        else:
            return render_template('trending.html', articles=articles, page=page,
                                per_page=per_page, pagination=pagination, articles_length=articles_length)
    except ValueError:        
        total = 0
        return render_template('trending.html', total=total)

# User Liked article
@app.route('/article_liked', methods=['POST'])
def article_liked():
    if current_user.is_authenticated():
        if request.method == "POST":
            article_list = request.get_json()
            article = article_list["article"]
            user = current_user.username
            likes = app.config['USERS_COLLECTION'].find_one({'_id': user})["likes"]
            if article in likes:
                return json.dumps({"status": 'Already exists'})
            else:
                likes.append(article)
                app.config['USERS_COLLECTION'].update({"_id": user}, {"$set": {"likes": likes}})
                ts = time.time()
                data = {
                    "url": article,
                    "user": current_user.username,
                    "createdAt":  datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                }
                app.config['LIKES_COLLECTION'].insert(data)
                return json.dumps({'status':'OK'});
    else:
        flash("Login to submit a link", category="error")
        return redirect(request.args.get("login") or url_for("login"))

# User Unliked article
@app.route('/article_unliked', methods=['POST'])
def article_unliked():
    if current_user.is_authenticated():
        if request.method == "POST":
            article_list = request.get_json()
            article = article_list["article"]
            user = current_user.username
            likes = app.config['USERS_COLLECTION'].find_one({'_id': user})["likes"]
            if article in likes:
                app.config['USERS_COLLECTION'].update({"_id": user}, {"$pull": {"likes": article}})
                app.config['LIKES_COLLECTION'].remove({"user": user, "url": article})
                return json.dumps({"status": 'Successfully removed'})
            else:
                return json.dumps({'status':'Article not in the list'});
    else:
        flash("Login to submit a link", category="error")
        return redirect(request.args.get("login") or url_for("login"))