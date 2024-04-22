import boto3
import uuid
import logging
import traceback
from datetime import datetime
from flask import Flask, request, session, redirect, render_template, make_response, jsonify
from flask_session import Session

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

AWSKEY = ''
AWSSECRET = ''
PUBLIC_BUCKET = ''
DYNAMO_TABLE = ''
STORAGE_URL = f''

dynamodb = boto3.resource('dynamodb',
                          region_name= "us-east-1",
                          aws_access_key_id= AWSKEY,
                          aws_secret_access_key= AWSSECRET)


def get_table(name):
    dynamodb = boto3.resource(service_name='dynamodb', region_name='us-east-1',
                              aws_access_key_id=AWSKEY, aws_secret_access_key=AWSSECRET)
    table = dynamodb.Table(name)
    return table
@app.route('/')
def home():
    if is_logged_in():
        return redirect("account.html")
    return render_template("login.html")

@app.route('/thing')
def thing():
    return session["thing"]


@app.route('/login')
def login():
    email = request.args.get("email")
    password = request.args.get("password")

    table = get_table("Users")
    item = table.get_item(Key={"email": email})

    if 'Item' not in item:
        return {"results": "Email not found."}

    user = item['Item']

    if password != user["password"]:
        return {"result": " Password does not match."}

    session["email"] = user["email"]
    session["username"] = user["username"]

    result = {"result": "OK"}
    response = make_response(result)
    remember = request.args.get("remember")
    if (remember == "no"):
        response.delete_cookie("remember")
    else:
        key = add_remember_key(user["email"])
        response.set_cookie("remember", key, max_age = 60*60*24*14)
    return response

def is_logged_in():
    if not session.get("email"):
        return auto_login()
    return True


@app.route('/account.html')
def account():
    if not is_logged_in():
        return redirect("/")
    return render_template("account.html", username = session["username"])

@app.route('/logout.html')
def logout():
    session.pop("email", None)
    session.pop("username", None)

    response = make_response(redirect("/"))
    response.delete_cookie("remember")
    return response

def add_remember_key(email):
    table = get_table("Remember")
    key = str(uuid.uuid4()) + str(uuid.uuid4()) + str(uuid.uuid4())
    item = {"key":key, "email":email}
    table.put_item(Item=item)
    return key

def auto_login():
    cookie = request.cookies.get("remember")
    if cookie is None:
        return False

    table = get_table("Remember")
    result = table.get_item(Key={"key":cookie})
    if 'Item' not in result:
        return False

    remember = result['Item']

    table = get_table("Users")
    result = table.get_item(Key={"email":remember["email"]})

    user = result['Item']
    session["email"] = user["email"]
    session["username"] = user["username"]

@app.route('/add_entry', methods=['POST'])
def add_entry():
    if not session.get("email"):
        return jsonify({'success': False, 'error': 'User not logged in'}), 401

    title = request.form['title']
    text = request.form['text']
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    table = get_table("blogposts")
    post_id = str(uuid.uuid4())

    table.put_item(Item={
        'post_id': post_id,
        'title': title,
        'text': text,
        'date': date
    })

    return jsonify({'success': True, 'redirect_url': '/editor'})

@app.route('/entries', methods=['GET'])
def get_entries():
    table = get_table("blogposts")
    try:
        response = table.scan()
        entries = response['Items']
        entries.sort(key=lambda x: x['date'], reverse=True)
        app.logger.debug(f"Entries fetched: {entries}")
    except Exception as e:
        app.logger.error(f"Failed to fetch entries: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch entries'}), 500

    if not session.get("email"):
        return jsonify({'entries': entries}), 200
    else:
        return jsonify({'entries': entries, 'logged_in': True}), 200

@app.route('/delete_entry', methods=['POST'])
def delete_entry():
    if not session.get("email"):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    data = request.get_json()
    post_id = data['post_id']

    try:
        table = get_table(DYNAMO_TABLE)
        table.delete_item(Key={'post_id': post_id})
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/editor')
def editor():
    if 'email' not in session:
        return redirect("/login")

    username = session.get("username", "Guest")
    table = get_table("blogposts")
    response = table.scan()
    entries = response['Items']
    entries.sort(key=lambda x: x['date'], reverse=True)

    return render_template("editor.html", username=username, entries=entries)

@app.route('/register', methods=['POST'])
def register_user():
    try:
        data = request.get_json()
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')

        table = get_table('Users')

        existing_user = table.get_item(Key={'email': email})
        if 'Item' in existing_user:
            return jsonify({'error': 'User already exists'}), 409

        table.put_item(Item={
            'email': email,
            'username': username,
            'password': password
        })
        return jsonify({'success': True}), 200

    except Exception as e:
        error_message = f"Error in /register: {str(e)}"
        logging.error(error_message)
        logging.error(traceback.format_exc())
        return jsonify({'error': 'Server error', 'message': error_message}), 500

@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'email' not in session:
        return jsonify({'error': 'Unauthorized access'}), 403

    table = get_table('Users')
    email = session['email']

    try:
        table.delete_item(Key={'email': email})
        session.pop('email', None)
        return jsonify({'success': 'Account deleted successfully'}), 200
    except Exception as e:
        app.logger.error(f"Error deleting user account: {e}")
        return jsonify({'error': 'Failed to delete account'}), 500


if __name__ == '__main__':
    app.run(debug=True)
