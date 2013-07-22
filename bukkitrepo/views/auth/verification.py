from flask import render_template, abort
from bukkitrepo.models import BRConnection
from bukkitrepo.email import Message


def resend_verification(email=None):
    conn_mgr = BRConnection()
    users = conn_mgr.users

    user = users.find_one({'email': email})

    if email is None:
        abort(404)

    if user is None:
        abort(404)

    content = '''
      <h1>Account verification</h1>
      <p>In order to use your Bukkit Repo account, you need to verify your email address. The good news is that it's easy. Just click the link below!</p>
      http://bukkitrepo.me/verification/verify/{0}
    '''.format(user['verification_key'])

    subject = 'Verify your bukkitrepo account'
    from_email = 'no-reply@bukkitrepo.me'
    from_name = 'Bukkit Repo Staff'
    to_email = email
    to_name = user['name']

    email = Message(subject, content, from_email, from_name, to_email, to_name)

    if not user['verified']:
        email.send()
        return render_template('page.html', page_content='<h3>Resend Verification</h3><p>I\'ve sent another verification email to {0}.</p>'.format(email))
    else:
        return render_template('page.html', page_content='<h3>Resend Verification</h3><p>Your email address is already verified, silly!</p>')


def verify_user(verification_key=None):
    conn_mgr = ConnectionManager()
    users = conn_mgr.users

    user = users.find_one({'verification_key': verification_key})

    if verification_key is None:
        abort(404)

    if user is None:
        return render_template('page.html', page_content='<h3>Verification</h3><p>You supplied an invalid verification key!</p>')

    if user['verified']:
        return render_template('page.html', page_content='<h3>Verification</h3><p>Your account has already been verified.</p>')

    users.update({'verification_key': verification_key}, {'$set': {'verified': True}})
    return render_template('page.html', page_content='<h3>Verification</h3><p>Congratulations {0}! You have been verified! Now you may log in.</p>'.format(user['name']))
