from darecms.common import *


def valid_password(password, account):
    pr = account.password_reset
    if pr and pr.is_expired:
        account.session.delete(pr)
        pr = None
    all_hashed = [account.hashed] + ([pr.hashed] if pr else [])
    return any(bcrypt.hashpw(password.encode('utf-8'), hashed.encode('utf-8')) == hashed.encode('utf-8') for hashed in all_hashed)


@all_renderable()
class Root:

    def index(self):
        return {}

    def invalid(self, **params):
        return {
            'message': params.get('message')
        }

    def login(self, session, message='', original_location=None, **params):
        original_location = create_valid_user_supplied_redirect_url(original_location, default_url='../accounts/')

        if 'email' in params:
            try:
                account = session.get_account_by_email(params['email'])
                if not valid_password(params['password'], account):
                    message = 'Incorrect password'
            except NoResultFound:
                message = 'No account exists for that email address'

            if not message:
                cherrypy.session['account_id'] = account.id
                cherrypy.session['csrf_token'] = uuid4().hex
                raise HTTPRedirect(original_location)

        return {
            'message': message,
            'email': params.get('email', ''),
            'original_location': original_location,
        }