from app import app, lm
from flask import request, redirect, render_template, url_for, flash, current_app
from flask.ext.login import login_user, logout_user, login_required, current_user
from flask.ext.paginate import Pagination

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

# Implementation of a method to puluralize words based on count value given in the parameter
def pularize(count, word):
    if count < 2:
        return str(count) + ' ' + word + ' ago'
    else:
        return str(count) + ' ' + word +'s ' + 'ago'


# Method to get the page items
def get_page_items():
    page = int(request.args.get('page', 1))
    per_page = request.args.get('per_page')
    if not per_page:
        per_page = current_app.config.get('PER_PAGE', 10)
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

# These methods are internally used in this class 
# Method to get the CSS Framework
def get_css_framework():
    return current_app.config.get('CSS_FRAMEWORK', 'BOOTSTRAP3')

# Method to get the link sizes
def get_link_size():
    return current_app.config.get('LINK_SIZE', 'sm')

# Method to choose single page output or multi page output
def show_single_page_or_not():
    return current_app.config.get('SHOW_SINGLE_PAGE', False)

# Method to get articles length and articles 
def articles_stat(collection, sortby):
    page, per_page, offset = get_page_items()
    sort = [(sortby, -1)]
    query_result = app.config[collection].find().sort(sort)
    articles = query_result.skip(offset).limit(per_page)
    articles_length = articles.count() if articles else 0
    return articles, articles_length, page, per_page, offset
        
# Method to get count of articles
def get_count(collection):
    return app.config[collection].find().count()

# Method to get custom query results
def get_articles(collection, condition_key, condition_value):
    page, per_page, offset = get_page_items()
    sort = [("createdAt", -1)]
    query_result = app.config[collection].find({condition_key: condition_value}).sort(sort)
    articles = query_result.skip(offset).limit(per_page)
    articles_length = articles.count() if articles else 0
    return articles, articles_length, page, per_page, offset