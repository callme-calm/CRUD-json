import identity
import identity.web
import requests
from flask import Flask, redirect, render_template, request, session, url_for
from flask_session import Session

import app_config

app = Flask(__name__)
app.config.from_object(app_config)
Session(app)

# This section is needed for url_for("foo", _external=True) to automatically
# generate http scheme when this sample is running on localhost,
# and to generate https scheme when it is deployed behind reversed proxy.
# See also https://flask.palletsprojects.com/en/2.2.x/deploying/proxy_fix/
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

auth = identity.web.Auth(
    session=session,
    authority=app.config.get("AUTHORITY"),
    client_id=app.config["CLIENT_ID"],
    client_credential=app.config["CLIENT_SECRET"],
)


@app.route("/login")
def login():
    return render_template("login.html", version=identity.__version__, **auth.log_in(
        scopes=app_config.SCOPE, # Have user consent to scopes during log-in
        redirect_uri=url_for("auth_response", _external=True), # Optional. If present, this absolute URL must match your app's redirect_uri registered in Azure Portal
        ))


@app.route(app_config.REDIRECT_PATH)
def auth_response():
    result = auth.complete_log_in(request.args)
    if "error" in result:
        return render_template("auth_error.html", result=result)
    return redirect(url_for("index1"))


@app.route("/logout")
def logout():
    return redirect(auth.log_out(url_for("index1", _external=True)))


@app.route("/")
def index1():
    if not (app.config["CLIENT_ID"] and app.config["CLIENT_SECRET"]):
        # This check is not strictly necessary.
        # You can remove this check from your production code.
        return render_template('config_error.html')
    if not auth.get_user():
        return redirect(url_for("login"))
    return render_template('index1.html', user=auth.get_user())


@app.route("/call_downstream_api")
def call_downstream_api():
    token = auth.get_token_for_user(app_config.SCOPE)
    if "error" in token:
        return redirect(url_for("login"))
    # Use access token to call downstream api
    api_result = requests.get(
        app_config.ENDPOINT,
        headers={'Authorization': 'Bearer ' + token['access_token']},
        timeout=30,
    ).json()
    return render_template('display.html', result=api_result)
import json

with open("static/json_data.json",'r') as f:
    books=json.load(f)

@app.route('/books', methods=['GET'])
def get_book():
    token = auth.get_token_for_user(app_config.SCOPE)
    if "error" in token:
        return redirect(url_for("login"))

    with open("static/json_data.json", 'r') as f:
        latest_books = json.load(f)
    return render_template('index1.html',books=latest_books)
    # return json.dumps(books)

@app.route('/books/add', methods=['GET','POST'])
def create_book():
    token = auth.get_token_for_user(app_config.SCOPE)
    if "error" in token:
        return redirect(url_for("login"))

    if request.method == 'GET':
        return render_template("add_book.html")
    # return json.dumps(books)
    new_book = request.json
    # return f"{new_book} ------ {books}"
    global books
    with open("static/json_data.json", 'r') as f:
        books = json.load(f)
    books.append(new_book)

    rewrite_file(books)
    return json.dumps(new_book), 201

@app.route('/books/<book_id>/update', methods=['GET','PATCH'])
def update_book(book_id):
    token = auth.get_token_for_user(app_config.SCOPE)
    if "error" in token:
        return redirect(url_for("login"))
    global books
    with open("static/json_data.json", 'r') as f:
        books = json.load(f)
    if request.method == 'GET':
        return render_template("update_book.html",book_id=book_id,books=books)
    new_book = request.json


    # books.append(new_book)

    for book in books:
        if int(book['id']) == int(book_id) :
            book.update(request.json)

    rewrite_file(books)
    return redirect(url_for('get_book'))
    # return "error", 404

@app.route('/books/<id>/delete', methods=['POST'])
def delete_book(id):
    token = auth.get_token_for_user(app_config.SCOPE)
    if "error" in token:
        return redirect(url_for("login"))

    # return f"{id},{books[0]['id'],id==int(books[0]['id'])},{type(id)} , {type(books[0]['id'])}"
    new_books = []
    for book in books:
        if int(book['id']) != int(id):
            new_books.append(book)
    rewrite_file(new_books)

    # return json.dumps(new_books)
    return redirect(url_for('get_book'))



def rewrite_file(new_books):
    with open('static/json_data.json', 'w') as f:
        f.write(json.dumps(new_books, indent=4))


if __name__ == "__main__":
    app.run(debug=True)
