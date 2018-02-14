from collections import Counter, namedtuple
from flask import Flask, request, redirect, render_template, Markup, flash
import plotly.offline as pyoffline
import plotly.graph_objs as go
import re
import secrets
import os

# setup Flask
app = Flask(__name__)
assert os.path.exists('secret.key')
with open('secret.key', 'rb') as key_file:
    app.secret_key = key_file.read()

# define a user tuple with username and page view count
User = namedtuple('User', ['name', 'count'])

# regex to match the first seven fields of the log file format
log_line_re = re.compile(b'^\d+? \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} ".+?" \d+? [\d.]+? (?P<username>.+?)\s')


def get_top_users(input_file, n=10):
    """
    Given a file object count the number of page views for each username
    :param input_file: a python file object
    :param n: the number of top users to return
    :return: a list of tuples of (name, count)
    """
    count = Counter()

    for line in input_file:
        if line.startswith(b'#'):
            continue

        match = log_line_re.match(line)
        if not match:
            continue
        username = match.group('username').decode()
        count.update([username])

    return count.most_common(n)


def get_pie_chart_embed(names, counts):
    """
    Given a list of names and a list of counts return a div element with a plot.ly pie chart
    :param names: a list of usernames
    :param counts: a list of counts
    :return: a div element
    """
    pie_chart = go.Pie(labels=names, values=counts)
    return pyoffline.plot(
        [pie_chart],
        output_type='div'
    )


@app.route('/')
def index():
    """
    :return: the root index template
    """
    return render_template('index.html')


@app.route('/results', methods=['GET', 'POST'])
def results():
    """
    The form in the root index will post to this url
    :return: a page with the results from parsing the log file
    """
    if request.method == 'POST':
        if 'file-button' not in request.files:
            flash('You did not upload a file. Please upload a log file.')
            return redirect('/')
        uploaded_file = request.files['file-button']
        if uploaded_file.filename == '':
            flash('The uploaded filename was empty. Please upload a log file.')
            return redirect('/')

        if uploaded_file:
            top_users = get_top_users(uploaded_file)
            top_users_list = []
            names = []
            counts = []
            for element in top_users:
                name, count = element
                names.append(name)
                counts.append(count)
                top_users_list.append(User(name, count))

            return render_template(
                'results.html',
                users=top_users_list,
                chart=Markup(get_pie_chart_embed(names, counts))
            )

    flash('You did not upload a file. Please upload a log file')
    return redirect('/')

