import random
import re
import string
from flask import redirect, session, render_template, request
from passlib.handlers.sha2_crypt import sha512_crypt
from recaptcha.client import captcha
from bukkitrepo import app, CONFIG
from bukkitrepo.accounts.verification import resend_verification
from bukkitrepo.models import BRConnection, User


def redirect_to_login():
    return redirect('/login')


def redirect_to_home():
    return redirect('/')


def get_id(user_email):
    conn = BRConnection()
    users = conn.users
    user = users.find_one({'email': user_email})
    if user is None:
        return None
    return user['_id']


def get_user(id):
    conn = BRConnection()
    users = conn.users
    user = users.find_one({'_id': id})
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

    user = users.find_one({'_id': user_id})
    if user is None:
        return False

    password_hashed = sha512_crypt.encrypt(new_pass)
    users.update({'_id': user_id}, {'$set': {'password': password_hashed}})

    return True


def change_email(user_id, new_email):
    conn = BRConnection()
    users = conn.users

    user = users.find_one({'_id': user_id})
    if user is None:
        return False

    users.update({'_id': user_id}, {'$set': {'email': new_email}})

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
            return render_template('login.html', errors=['Either your email or password is incorrect.'])

        if not user['verified']:
            return render_template('login.html', errors=['You need to click the link in your verification email. If you need me to send another verification email for you, please click <a href="/verification/resend/{0}">here</a>.'.format(params['email'])])

        if sha512_crypt.verify(params['password'], user['password']):
            session['_id'] = user['_id']
            return redirect('/')
        else:
            return render_template('login.html', errors=['Either your email or password is incorrect.'])

    return render_template('login.html')


def forgot():
    return render_template('forgot.html')


def reset(reset_code=None):
    return render_template('reset.html')


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
        return account(successes=['Your email has been successfully changed to {0}.'.format(new_email)])
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
        user = users.find_one({'_id': session['_id']})
        deleted_users.insert(user)
        users.remove({'_id': session['_id']})

        return redirect('/logout')
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
        for key, value in results.iteritems():
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

        captcha_response = captcha.submit(
            request.form['recaptcha_challenge_field'],
            request.form['recaptcha_response_field'],
            CONFIG['recaptcha_private_key'],
            request.remote_addr
        )

        if not captcha_response.is_valid:
            error_list.append('The captcha answer you provided isn\'t correct.')
            errors = True

        if errors:
            return render_template('register.html', errors=error_list)

        password_hashed = sha512_crypt.encrypt(results['password'])

        verification_key = ''.join(random.choice(string.letters) for i in xrange(32))

        conn = BRConnection()
        users = conn.users

        for _ in users.find({'email': results['email']}):
            return render_template('register.html', errors=['There is already a user with the email {0}. Maybe you already signed up?'.format(results['email'])])

        new_user = User(email=results['email'], name=results['name'], password=password_hashed, verification_key=verification_key)
        users.insert(new_user.data)

        resend_verification(results['email'])

        return render_template('register_success.html', name=results['name'])

    return render_template('register.html')
