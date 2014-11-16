import sys
import config
import tweepy
from flask import Flask, render_template, request, redirect, url_for

#init tweepy
try:
    auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
    auth.set_access_token(config.access_token, config.access_token_secret)
    twitter = tweepy.API(auth)
    print "Skipped Twitter"
except:
    print "Twitter authentication failed!"
    sys.exit(1)

# init Flask
app = Flask(__name__)


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


@app.route('/answers')
def answers():
    return render_template('answers.html')


@app.route('/faq')
def faq():
    return render_template('faq.html')


@app.route('/ask', methods=['POST', 'GET'])
def doAsk():
    try:
        if request.method == 'POST':
            question = request.form.get('q')

            # Validate length
            if len(question) > 130:
                raise

            # Send to Twitter
            result = twitter.update_status('@' + config.SCREENNAME + ' ' + question)

            tweet_id = result.id_str


            # TODO persist in database

        return redirect('/?asked=1')
    except Exception as e:
        return redirect('/?error=1')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
