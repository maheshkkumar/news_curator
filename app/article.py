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
from dependency import get_pagination, get_page_items, chunks, article_categories, pularize, get_css_framework

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

