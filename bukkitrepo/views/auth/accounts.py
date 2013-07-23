import random
import re
import string
import requests
from flask import redirect, session, render_template, request, abort
from passlib.handlers.sha2_crypt import sha512_crypt
from bukkitrepo import app, CONFIG
from bukkitrepo.views.auth.verification import resend_verification
from bukkitrepo.models import BRConnection, User, ResetKey
from bukkitrepo.email import Message
from bson.objectid import ObjectId


def redirect_to_login():
    return redirect('/account/sign_in/')


def redirect_to_home():
    return redirect('/')


def get_id(user_email):
    conn = BRConnection()
    users = conn.users
    user = users.find_one({'email': user_email})
    if user is None:
        return None
    return str(user['_id'])


def get_user(user_id):
    conn = BRConnection()
    users = conn.users
    user = users.find_one({'_id': ObjectId(user_id)})
    return user


def check_password(user_id, password):
    user = get_user(user_id)
    if user is None:
        return None

    return sha512_crypt.verify(password, user['password'])


def get_email(user_id):
    user = get_user(user_id)
    if user is None:
        return None

    return user['email']


def get_name(user_id):
    user = get_user(user_id)
    if user is None:
        return None

    return user['name']


@app.context_processor
def user_info():
    info = {}
    if '_id' in session:
        user_id = session['_id']

        info['logged_in'] = True
        info['email'] = get_email(user_id)
        info['name'] = get_name(user_id)
        return info
    else:
        info['logged_in'] = False
        return info


def change_password(user_id, new_pass):
    conn = BRConnection()
    users = conn.users

    user = get_user(user_id)
    if user is None:
        return False

    password_hashed = sha512_crypt.encrypt(new_pass)
    users.update({'_id': ObjectId(user_id)}, {'$set': {'password': password_hashed}})

    return True


def change_email(user_id, new_email):
    conn = BRConnection()
    users = conn.users

    user = get_user(user_id)
    if user is None:
        return False

    users.update({'_id': ObjectId(user_id)}, {'$set': {'email': new_email, 'verified': False}})
    resend_verification(new_email)
    logout()

    return True


def login():
    if '_id' in session:
        return redirect_to_home()

    if request.method == 'POST':
        params = {
            'email': request.form['email'],
            'password': request.form['password']
        }

        conn = BRConnection()
        users = conn.users

        user = users.find_one({'email': params['email']})
        if user is None:
            return render_template('sign_in.html', errors=['Either your email or password is incorrect.'])

        if not user['verified']:
            return render_template('sign_in.html', errors=['You need to click the link in your verification email. If you need me to send another verification email for you, please click <a href="/verification/resend/{0}">here</a>.'.format(params['email'])])

        if sha512_crypt.verify(params['password'], user['password']):
            session['_id'] = str(user['_id'])
            return redirect('/')
        else:
            return render_template('sign_in.html', errors=['Either your email or password is incorrect.'])

    return render_template('sign_in.html')


def forgot():
    if '_id' in session:
        return redirect_to_home()

    if request.method == "POST":
        conn_mgr = BRConnection()
        reset_keys = conn_mgr.reset_keys

        email = request.form['email']
        errors = []

        if not email:
            errors.append('Please enter an email address!')

        user = get_user(get_id(email))
        if not user:
            errors.append('The email address you entered did not match any accounts.')

        if errors:
            return render_template('forgot.html', errors=errors)

        key = ''.join(random.choice(string.ascii_lowercase + string.digits) for i in range(32))
        reset_key = ResetKey(user['_id'], key)

        reset_keys.insert(reset_key.data)

        content = '''
        <h1>Reset password</h1>
        <p>Bukkit Repo has recieved a request to reset the password of the Bukkit Repo account under this email address. If you did not make this request, you can disregard this email. To reset your password, please click the link below.</p>
        http://bukkitrepo.me/account/forgot/reset/{0}
        '''.format(key)

        subject = 'Reset your bukkitrepo password'
        from_email = 'no-reply@bukkitrepo.me'
        from_name = 'Bukkit Repo Staff'
        to_email = user['email']
        to_name = user['name']

        email = Message(subject, content, from_email, from_name, to_email, to_name)

        email.send()

        return render_template('page.html', page_content='A link that can be used to reset the password for this account has been sent to your email address.')
    else:
        return render_template('forgot.html')


def get_user_from_reset_key(reset_key):
    conn = BRConnection()
    reset_keys = conn.reset_keys
    users = conn.users

    key_obj = reset_keys.find_one({'key': reset_key})
    if key_obj is None:
        return None

    user_object_id = key_obj['user']
    return users.find_one({'_id': user_object_id})


def reset(reset_code=None):
    conn = BRConnection()
    reset_keys = conn.reset_keys

    if '_id' in session:
        return redirect_to_home()

    if not reset_code:
        abort(404)

    user = get_user_from_reset_key(reset_code)
    if not user:
        abort(404)

    if reset_keys.find_one({'key': reset_code})['used']:
        return render_template('page.html', page_content='The reset key that you tried to use has already been used.')

    if request.method == 'POST':

        new_password = request.form['password']
        change_password(str(user['_id']), new_password)
        reset_keys.update({'key': reset_code}, {'$set': {'used': True}})

        return render_template('page.html', page_content='Your password has successfully been reset. You may now sign in.')
    else:
        return render_template('password_reset.html', email_of_account_being_reset=user['email'])


def logout():
    if not '_id' in session:
        return redirect_to_login()

    session.pop('_id', None)
    return redirect_to_home()


def account(alerts=None, successes=None, errors=None):
    if not '_id' in session:
        return redirect_to_login()

    if alerts is not None:
        return render_template('account.html', alerts=alerts)

    if successes is not None:
        return render_template('account.html', successes=successes)

    if errors is not None:
        return render_template('account.html', errors=errors)

    return render_template('account.html')


def user_change_email():
    if not '_id' in session:
        return redirect_to_login()

    new_email = request.form['email']

    if check_password(session['_id'], request.form['old_password']):
        conn = BRConnection()
        users = conn.users

        for _ in users.find({'email': new_email}):
            return account(errors=['There is already a user with the email {0}.'.format(new_email)])

        change_email(session['_id'], new_email)
        logout()
        return render_template('page.html', page_content='Your email has been successfully changed to {0}. Please verify this email address before signing in again.'.format(new_email))
    else:
        return account(errors=['Your specified an incorrect password.'])


def user_change_password():
    if not '_id' in session:
        return redirect_to_login()

    new_pass = request.form['password']

    if check_password(session['_id'], request.form['old_password']):
        change_password(session['_id'], new_pass)
        return account(successes=['Your password has been successfully changed.'])
    else:
        return account(errors=['Your specified an incorrect password.'])


def user_delete():
    if not '_id' in session:
        return redirect_to_login()

    conn = BRConnection()
    users = conn.users
    deleted_users = conn.deleted_users

    if check_password(session['_id'], request.form['password']):
        user = get_user(session['_id'])
        deleted_users.insert(user)
        users.remove({'_id': ObjectId(session['_id'])})

        return redirect('/account/log_out')
    else:
        return account(errors=['Your specified an incorrect password.'])


def register():
    if '_id' in session:
        return redirect_to_home()

    if request.method == 'POST':
        results = {
            'name': request.form['name'],
            'email': request.form['email'],
            'password': request.form['password']
        }

        # Time to validate the shit out of this thing
        error_list = []
        errors = False
        for key, value in results.items():
            if not value:
                error_list.append('Please specify a {0}!'.format(key.replace('_', ' ')))
                errors = True

            if key == 'email':
                if not re.match(r'[^@]+@[^@]+\.[^@]+', value):
                    error_list.append('Please specify a valid email address!')
                    errors = True

            if isinstance(value, str):
                if len(value) > 50:
                    error_list.append('The length of {0} cannot exceed 50.'.format(key.replace('_', ' ')))
                    errors = True

        captcha_payload = {'privatekey': CONFIG['recaptcha_private_key'],
                           'remoteip': request.remote_addr,
                           'challenge': request.form['recaptcha_challenge_field'],
                           'response': request.form['recaptcha_response_field']}
        captcha_response = requests.post('http://www.google.com/recaptcha/api/verify', captcha_payload)

        if 'true' not in captcha_response.text:
            error_list.append('The captcha answer you provided isn\'t correct.')
            errors = True

        if errors:
            return render_template('register.html', errors=error_list)

        password_hashed = sha512_crypt.encrypt(results['password'])

        verification_key = ''.join(random.choice(string.ascii_lowercase + string.digits) for i in range(32))

        conn = BRConnection()
        users = conn.users

        for _ in users.find({'email': results['email']}):
            return render_template('register.html', errors=['There is already a user with the email {0}. Maybe you already signed up?'.format(results['email'])])

        new_user = User(email=results['email'], name=results['name'], password=password_hashed, verification_key=verification_key)
        users.insert(new_user.data)

        resend_verification(results['email'])

        return render_template('register_success.html', name=results['name'])

    return render_template('register.html')
