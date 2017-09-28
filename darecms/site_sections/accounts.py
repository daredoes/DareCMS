from darecms.common import *


def valid_password(password, account):
    pr = account.password_reset
    if pr and pr.is_expired:
        account.session.delete(pr)
        pr = None
    all_hashed = [account.hashed] + ([pr.hashed] if pr else [])
    return any(bcrypt.hashpw(password.encode('utf-8'), hashed.encode('utf-8')) == hashed.encode('utf-8') for hashed in all_hashed)


@all_renderable(c.ACCOUNTS)
class Root:
    def index(self, session, message=''):
        return {
            'message':  message,
            'accounts': session.query(AdminAccount).join(User).order_by(User.last_first).all(),
            'AdminAccount': AdminAccount,
            'users': session.query(User).filter(User.admin_account == None).order_by(User.last_first).all()
        }

    @csrf_protected
    def update(self, session, password='', message='', **params):
        account = session.admin_account(params, checkgroups=['access'])
        if account.is_new:
                password = password if password else genpasswd()
                account.hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        message = message or check(account)
        if not message:
            message = 'Account settings uploaded'
            account.user = session.user(account.user_id)   # dumb temporary hack, will fix later with tests
            session.add(account)
            if account.is_new:
                body = render('emails/accounts/new_account.txt', {
                    'account': account,
                    'password': password
                })
                send_email(c.ADMIN_EMAIL, session.user(account.user_id).email, 'New ' + c.EVENT_NAME + ' Account', body)

        raise HTTPRedirect('index?message={}', message)

    @csrf_protected
    def delete(self, session, id, return_to='', **params):
        session.delete(session.user(id))
        raise HTTPRedirect('{}?message={}', return_to if return_to else 'index', 'Account deleted')

    @site_mappable
    def all(self, session, message='', page='0', search_text='', uploaded_id='', order='last_first', invalid='', **params):
        # DEVELOPMENT ONLY: it's an extremely convenient shortcut to show the first page
        # of search results when doing testing. it's too slow in production to do this by
        # default due to the possibility of large amounts of reg stations accessing this
        # page at once. viewing the first page is also rarely useful in production when
        # there are thousands of attendees.
        if c.DEV_BOX and not int(page):
            page = 1
        users = session.query(User)
        total_count = users.count()
        count = 0
        search_text = search_text.strip()
        if search_text:
            users = session.search(search_text)
            count = users.count()

        users = users.order(order)

        page = int(page)
        if search_text:
            page = page or 1
            if search_text and count == total_count and total_count != 1:
                message = 'No matches found'
            elif search_text and count == 1:
                raise HTTPRedirect('form?id={}&message={}', users.one().id, 'This attendee was the only search result')

        pages = range(1, int(math.ceil(count / 100)) + 1)
        users = users[-100 + 100*page: 100*page] if page else []

        return {
            'message':        message if isinstance(message, str) else message[-1],
            'page':           page,
            'pages':          pages,
            'invalid':        invalid,
            'search_text':    search_text,
            'search_results': bool(search_text),
            'users':          users,
            'order':          Order(order),
            'user_count':     total_count,
            'user':           session.user(uploaded_id, allow_invalid=True) if uploaded_id else None
        }

    def form(self, session, message='', return_to='', **params):
        user = session.user(params, checkgroups=User.all_checkgroups, bools=User.all_bools)
        if 'first_name' in params:
            message = ''
            if not message:
                message = check(user)
            session.add(user)
            msg_text = '{} has been saved'.format(user.full_name)
            if params.get('save') == 'save_return_to_search':
                if return_to:
                    raise HTTPRedirect(return_to + '&message={}', 'Attendee data saved')
                else:
                    raise HTTPRedirect('index?uploaded_id={}&message={}&search_text={}', user.id, msg_text,
                        '{} {}'.format(user.first_name, user.last_name) if c.AT_THE_CON else '')
            else:
                raise HTTPRedirect('form?id={}&message={}&return_to={}', user.id, msg_text, return_to)

        return {
            'message': message,
            'user': user
        }

    def address_book(self, id=None, session=None, message='', new_entry=None, **params):
        user = None
        if id:
            params['id'] = id
        address = session.address(params, ignore_csrf=True)


        if 'user_id' in params:
            user = session.user(params['user_id'])
            if 'add' in params:
                message = check(address)
                if not message:
                    session.add(address)
                    session.commit()
                message = 'Address Saved'

        else:
            raise HTTPRedirect("../")



        return {
            'user': user,
            'address': address,
            'message': message,
            'id': id,
            'new_entry': True if new_entry else False
        }

    @unrestricted
    def insert_test_admin(self, session):
        if session.insert_test_admin_account():
            msg = "Test admin account created successfully"
        else:
            msg = "Not allowed to create admin account at this time"

        raise HTTPRedirect('login?message={}', msg)

    @unrestricted
    def login(self, session, message='', original_location=None, **params):
        original_location = create_valid_user_supplied_redirect_url(original_location, default_url='homepage')

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
            'email':   params.get('email', ''),
            'original_location': original_location,
        }

    @unrestricted
    def homepage(self, message=''):
        if not cherrypy.session.get('account_id'):
            raise HTTPRedirect('login?message={}', 'You are not logged in')
        return {'message': message}

    @unrestricted
    def info(self, session, message='', id='', **params):
        try:
            user = session.query(User).filter(User.id == id).first()
        except sqlalchemy.exc.StatementError:
            user = None
        if not user:
            user = c.CURRENT_ADMIN
        return {
            'user': user,
            'message': message
        }


    @unrestricted
    def error(self, session, message=''):
        message = session.query(AdminAccount).first()
        return {'message': message}

    @unrestricted
    def logout(self):
        for key in list(cherrypy.session.keys()):
            if key not in ['preregs', 'paid_preregs', 'job_defaults', 'prev_location']:
                cherrypy.session.pop(key)
        raise HTTPRedirect('login?message={}', 'You have been logged out')

    @unrestricted
    def sitemap(self):
        site_sections = cherrypy.tree.apps[c.PATH].root
        modules = {name: getattr(site_sections, name) for name in dir(site_sections) if not name.startswith('_')}
        pages = defaultdict(list)
        for module_name, module_root in modules.items():
            for name in dir(module_root):
                method = getattr(module_root, name)
                if getattr(method, 'exposed', False):
                    spec = inspect.getfullargspec(get_innermost(method))
                    if set(getattr(method, 'restricted', []) or []).intersection(AdminAccount.access_set()) \
                            and not getattr(method, 'ajax', False) \
                            and (getattr(method, 'site_mappable', False)
                              or len([arg for arg in spec.args[1:] if arg != 'session']) == len(spec.defaults or []) and not spec.varkw):
                        pages[module_name].append({
                            'name': name.replace('_', ' ').title(),
                            'path': '/{}/{}'.format(module_name, name)
                        })
        return {'pages': sorted(pages.items())}

    @unrestricted
    def reset(self, session, message='', email=None):
        if email is not None:
            try:
                account = session.get_account_by_email(email)
            except NoResultFound:
                message = 'No account exists for email address {!r}'.format(email)
            else:
                password = genpasswd()
                if account.password_reset:
                    session.delete(account.password_reset)
                    session.commit()
                session.add(PasswordReset(admin_account=account, hashed=bcrypt.hashpw(password, bcrypt.gensalt())))
                body = render('emails/accounts/password_reset.txt', {
                    'name': account.user.full_name,
                    'password':  password
                })
                send_email(c.ADMIN_EMAIL, account.user.email, c.EVENT_NAME + ' Admin Password Reset', body)
                raise HTTPRedirect('login?message={}', 'Your new password has been emailed to you')

        return {
            'email':   email,
            'message': message
        }

    def update_password_of_other(self, session, id, message='', updater_password=None, new_password=None,
                                 csrf_token=None, confirm_new_password=None):
        if updater_password is not None:
            new_password = new_password.strip()
            updater_account = session.admin_account(cherrypy.session['account_id'])
            if not new_password:
                message = 'New password is required'
            elif not valid_password(updater_password, updater_account):
                message = 'Your password is incorrect'
            elif new_password != confirm_new_password:
                message = 'Passwords do not match'
            else:
                check_csrf(csrf_token)
                account = session.admin_account(id)
                account.hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                raise HTTPRedirect('index?message={}', 'Account Password Updated')

        return {
            'account': session.admin_account(id),
            'message': message
        }

    @unrestricted
    def change_password(self, session, message='', old_password=None, new_password=None, csrf_token=None, confirm_new_password=None):
        if not cherrypy.session.get('account_id'):
            raise HTTPRedirect('login?message={}', 'You are not logged in')

        if old_password is not None:
            new_password = new_password.strip()
            account = session.admin_account(cherrypy.session['account_id'])
            if not new_password:
                message = 'New password is required'
            elif not valid_password(old_password, account):
                message = 'Incorrect old password; please try again'
            else:
                check_csrf(csrf_token)
                account.hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                raise HTTPRedirect('homepage?message={}', 'Your password has been updated')

        return {'message': message}

    @unrestricted
    def creative(self):
        return {

        }
