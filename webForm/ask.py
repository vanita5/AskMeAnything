import sys
import threading
import config
import tweepy
import sqlite3
import calendar
import datetime
import time
from flask_limiter import Limiter
from contextlib import closing
from flask import Flask, render_template, request, redirect, g
import logging
logging.basicConfig(filename='logfile.log',level=logging.DEBUG)

# #################
# INITIALIZATION #
##################

# init tweepy
try:
    auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
    auth.set_access_token(config.access_token, config.access_token_secret)
    twitter = tweepy.API(auth)
    ME = twitter.me()
except:
    print "Twitter authentication failed!"
    sys.exit(1)

# init Flask
app = Flask(__name__)
limiter = Limiter(app, global_limits=["200 per day", "50 per hour"])

###############
# FLASK BLOCK #
###############

@app.before_request
def before_request():
    g.db = connect_db()

    thread = getattr(g, 'thread', None)
    if thread is None:
        g.thread = AnswerDownloader()

    if not g.thread.isAlive():
        g.thread.start()


@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


@app.route('/', methods=['GET'])
def ask():
    asked = False
    error = False
    if request.method == 'GET':
        if request.values.get('asked') == '1':
            asked = True
        elif request.values.get('error') == '1':
            error = True

    return render_template('ask.html', name=config.USERNAME, asked=asked, error=error)


@app.route('/answers', defaults={'page': 1})
@app.route('/answers/<int:page>')
def answers(page):
    if not page or page <= 0:
        page = 1

    LIMIT = 10
    show_next = True
    show_previous = page != 1

    total = count_answers()
    start = (page - 1) * LIMIT

    if start >= total:
        start -= 1
    end = start + LIMIT

    next_start = start + LIMIT
    if next_start >= total:
        show_next = False
    answers = get_answers(start, end)
    return render_template('answers.html',
                           answers=answers,
                           screen_name=config.SCREENNAME,
                           show_next=show_next,
                           show_previous=show_previous,
                           page=page)


@app.route('/faq')
def faq():
    return render_template('faq.html')


@app.route('/doAsk', methods=['POST', 'GET'])
@limiter.limit("2/minute", key_func = lambda : request.environ['REMOTE_ADDR'])
def doAsk():
    try:
        if request.method == 'POST':
            question = request.form.get('q')

            # Validate length
            if len(question) > 130 or len(question) <= 0:
                raise

            # Send to Twitter
            result = twitter.update_status('@' + config.SCREENNAME + ' ' + question)

            # Save into database
            tweet_id = result.id
            timestamp_utc = calendar.timegm(result.created_at.utctimetuple())
            insert_question(tweet_id, question, timestamp_utc)


            # TODO persist in database

        return redirect('/ask?asked=1')
    except Exception as e:
        return redirect('/ask?error=1')


##################
# FUNCTION BLOCK #
##################

def connect_db():
    return sqlite3.connect(config.DATABASE)


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('../schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def insert_question(tweet_id, question, timestamp):
    g.db.execute('INSERT INTO questions(tweet_id, question, timestamp)\
                  VALUES (?, ?, ?)',
                 [tweet_id, question, timestamp])
    g.db.commit()


def insert_answer(q_id, answer, tweet_id, timestamp):
    with app.app_context():
        g.db = connect_db()
        g.db.execute('INSERT INTO answers(q_id, answer, tweet_id, timestamp)\
                      VALUES (?, ?, ?, ?)',
                     [q_id, answer, tweet_id, timestamp])
        g.db.commit()


def count_answers():
    cur = g.db.execute('SELECT COUNT(*)\
                        FROM answers a\
                        INNER JOIN questions q\
                        ON a.q_id = q.tweet_id')
    return cur.fetchall()[0][0]


def get_answers(start=0, end=5):
    cur = g.db.execute('SELECT q.question, q.author, q.timestamp, a.answer, a.tweet_id\
                        FROM answers a\
                        INNER JOIN questions q\
                        ON a.q_id = q.tweet_id\
                        ORDER BY id DESC\
                        LIMIT ' + str(start) + ', ' + str(end))
    return [dict(question=row[0],
                 author=row[1],
                 timestamp=datetime.datetime.fromtimestamp(int(row[2])),
                 answer=row[3],
                 tweet_id=row[4])
            for row in cur.fetchall()]


def get_since_id():
    try:
        with open('since_id', 'r') as f:
            return f.read()
    except:
        return ''


def save_since_id(since_id):
    with open('since_id', 'w') as f:
        f.write(str(since_id))


@app.errorhandler(429)
def ratelimit_handler(e):
    return render_template('ask.html', name=config.USERNAME, rate=1)


###############
# CLASS BLOCK #
###############

class AnswerDownloader(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True

    def run(self):
        try:
            while True:
                since_id = get_since_id()
                if len(since_id) > 0:
                    mentions = twitter.mentions_timeline(since_id)
                else:
                    mentions = twitter.mentions_timeline()

                for i in range(len(mentions) - 1, -1, -1):
                    tweet_id = mentions[i].id
                    timestamp_utc = calendar.timegm(mentions[i].created_at.utctimetuple())
                    q_id = mentions[i].in_reply_to_status_id

                    answer = mentions[i].text
                    my_screen_name = ME.screen_name
                    answer = answer.replace('@' + my_screen_name + ' ', '')
                    try:
                        insert_answer(q_id, answer, tweet_id, timestamp_utc)
                    except:
                        pass
                    if i == 0:
                        save_since_id(mentions[i].id)

                time.sleep(120)

        except Exception as e:
            logging.exception(e)



if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', debug=True)
