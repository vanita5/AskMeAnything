from flask import Flask, render_template, request

# init
app = Flask(__name__)


@app.route('/')
def ask():
    return render_template('ask.html')


@app.route('/answers')
def answers():
    return render_template('answers.html')


@app.route('/faq')
def faq():
    return render_template('faq.html')


@app.route('/ask', methods=['POST', 'GET'])
def doAsk():
    if request.method == 'POST':
        #TODO add question
        return None


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
