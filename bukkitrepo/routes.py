from bukkitrepo import app


# Import views
import bukkitrepo.views.projects
import bukkitrepo.views.auth.accounts
import bukkitrepo.views.auth.csrf

# Projects routes
app.add_url_rule('/', 'root_url', bukkitrepo.views.projects.index)
app.add_url_rule('/projects/', 'projects_index', bukkitrepo.views.projects.index)

# Authentication routes
app.add_url_rule('/account/register/', 'register', bukkitrepo.views.auth.accounts.register, methods=['GET', 'POST'])
app.add_url_rule('/account/sign_in/', 'sign_in', bukkitrepo.views.auth.accounts.login, methods=['GET', 'POST'])
app.add_url_rule('/account/log_out/', 'log_out', bukkitrepo.views.auth.accounts.logout)
app.add_url_rule('/account/', 'account', bukkitrepo.views.auth.accounts.account)
app.add_url_rule('/account/delete/', 'user_delete', bukkitrepo.views.auth.accounts.user_delete, methods=['POST'])
app.add_url_rule('/account/change/email/', 'user_change_email', bukkitrepo.views.auth.accounts.user_change_email, methods=['POST'])
app.add_url_rule('/account/change/password/', 'user_change_password', bukkitrepo.views.auth.accounts.user_change_password, methods=['POST'])
app.add_url_rule('/account/verification/resend/<email>/', 'resend_verification', bukkitrepo.views.auth.verification.resend_verification)
app.add_url_rule('/account/verification/verify/<verification_key>/', 'verify_user', bukkitrepo.views.auth.verification.verify_user)
app.add_url_rule('/account/forgot/', 'forgot', bukkitrepo.views.auth.accounts.forgot, methods=['GET', 'POST'])
app.add_url_rule('/account/forgot/reset/<reset_code>/', 'reset', bukkitrepo.views.auth.accounts.reset, methods=['GET', 'POST'])
