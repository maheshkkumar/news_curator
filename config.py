from pymongo import MongoClient

WTF_CSRF_ENABLED = True
SECRET_KEY = 'ABCDEFGHIJKLMNOPQRDTUVWXYZ12345678910'
DB_NAME = 'news_aggregator'

DATABASE = MongoClient()[DB_NAME]
NEWS_COLLECTION = DATABASE.news
ARTICLES_COLLECTION = DATABASE.articles
USERS_COLLECTION = DATABASE.users
LIKES_COLLECTION = DATABASE.likes

CATEGORIES = [  
                    ("AI","Artificial Intelligence"),
                    ("AYS", "Analytics"),
                    ("BD", "Big Data"),
                    ("BOOK", "Book"),
                    ("BLOG", "Blog"),
                    ("CAREER", "Career Related"),
                    ("COG", "Cognitive Science"),
                    ("CONF", "Conference"),
                    ("COMP", "Competitions"),
                    ("CV", "Computer Vision"),
                    ("DATA", "Dataset"),
                    ("DS", "Data Science"), 
                    ("DL","Deep Learning"),
                    ("DV", "Data Visualization"),
                    ("FB", "Facebook"),
                    ("FW", "Framework"),
                    ("HCI", "Human Computer Interaction"),
                    ("INDUS", "Industry"),
                    ("IPYTHON", "IPython Notebook"),
                    ("KAG", "Kaggle"),
                    ("MISC", "Miscellaneous"), 
                    ("ML", "Machine Learning"),
                    ("MATH", "Mathematics"),
                    ("NLP", "Natural Language Processing"),
                    ("NN", "Neural Networks"),
                    ("NVI", "Nvidia"),
                    ("PYT", "Python"), 
                    ("PROG", "Programming"),
                    ("STATS", "Statistics"),
                    ("SW", "Software Product"),
                    ("TUTS", "Tutorial"),
                    ("TWEET", "Twitter"),
                    ("WAR", "Versus"),
                    ("WS", "Web Scraping")
                ]

DEBUG = True

# email server
MAIL_SERVER = 'your.mailserver.com'
MAIL_PORT = 25
MAIL_USERNAME = 
MAIL_PASSWORD = None

# administrator list
ADMINS = ['you@example.com']