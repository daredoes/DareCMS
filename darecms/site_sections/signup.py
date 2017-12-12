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
    def index(self, session,  password='', message='', original_location=None, **params):
        original_location = create_valid_user_supplied_redirect_url(original_location, default_url='../soda')
        user = session.user(params, checkgroups=User.all_checkgroups, bools=User.all_bools)
        if user.is_new:
            message = check(user)
            if not message and 'first_name' in params:
                session.add(user)
                session.commit()
                password = password if password else genpasswd()
                admin_params = {
                    'access': '{}'.format(c.SODA),
                    'user_id': user.id,
                    'password': password
                }
                account = session.admin_account(admin_params, checkgroups=['access'])
                account.hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                message = check(account)
                if not message:
                    message = 'Account Created'
                    account.user = user
                    session.add(account)
                raise HTTPRedirect(original_location)
            return {
                'user': user
            }
        raise HTTPRedirect(original_location)
