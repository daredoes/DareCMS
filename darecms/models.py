from darecms.common import *


def _get_defaults(func):
    spec = inspect.getfullargspec(func)
    return dict(zip(reversed(spec.args), reversed(spec.defaults)))
default_constructor = _get_defaults(declarative.declarative_base)['constructor']


SQLAlchemyColumn = Column
sqlalchemy_relationship = relationship

def Column(*args, admin_only=False, **kwargs):
    """
    Returns a SQLAlchemy Column with the given parameters, except that instead
    of the regular defaults, we've overridden the following defaults if no
    value is provided for the following parameters:

        Field           Old Default     New Default
        -----           ------------    -----------
        nullable        True            False
        default         None            ''  (only for UnicodeText fields)
        server_default  None            <same value as 'default'>

    We also have an "admin_only" parameter, which is set as an attribute on
    the column instance, indicating whether the column should be settable by
    regular attendees filling out one of the registration forms or if only a
    logged-in admin user should be able to set it.
    """
    kwargs.setdefault('nullable', False)
    if args[0] is UnicodeText or isinstance(args[0], (UnicodeText, MultiChoice)):
        kwargs.setdefault('default', '')
    default = kwargs.get('default')
    if isinstance(default, (int, str)):
        kwargs.setdefault('server_default', str(default))
    col = SQLAlchemyColumn(*args, **kwargs)
    col.admin_only = admin_only or args[0] in [UUID, UTCDateTime]
    return col


def relationship(*args, **kwargs):
    """
    Returns a SQLAlchemy relationship with the given parameters, except that
    instead of the regular defaults, we've overridden the following defaults if
    no value is provided for the following parameters:
        load_on_pending now defaults to True
        cascade now defaults to 'all,delete-orphan'
    """
    kwargs.setdefault('load_on_pending', True)
    kwargs.setdefault('cascade', 'all,delete-orphan')
    return sqlalchemy_relationship(*args, **kwargs)


class utcnow(FunctionElement):
    """
    We have some tables where we want to save a timestamp on each row indicating
    when the row was first created.  Normally we could do something like this:

        created = Column(UTCDateTime, default=lambda: datetime.now(UTC))

    Unfortunately, there are some cases where we instantiate a model and then
    don't save it until sometime later.  This happens when someone registers
    themselves and then doesn't pay until later, since we don't save them to the
    database until they've paid.  Therefore, we use this class so that we can
    set a timestamp based on when the row was inserted rather than when the
    model was instantiated:

        created = Column(UTCDateTime, server_default=utcnow())

    The pg_utcnow and sqlite_utcnow functions below define the implementation
    for postgres and sqlite, and new functions will need to be written if/when
    we decided to support other databases.
    """
    type = UTCDateTime()


@compiles(utcnow, 'postgresql')
def pg_utcnow(element, compiler, **kw):
    return "timezone('utc', current_timestamp)"


@compiles(utcnow, 'sqlite')
def sqlite_utcnow(element, compiler, **kw):
    return "(datetime('now', 'utc'))"


class Choice(TypeDecorator):
    """
    Utility class for storing the results of a dropdown as a database column.
    """
    impl = Integer

    def __init__(self, choices, *, allow_unspecified=False, **kwargs):
        """
        choices: an array of tuples, where the first element of each tuple is
                 the integer being stored and the second element is a string
                 description of the value
        allow_unspecified: by default, an exception is raised if you try to save
                           a row with a value which is not in the choices list
                           passed to this class; set this to True if you want to
                           allow non-default values
        """
        self.choices = dict(choices)
        self.allow_unspecified = allow_unspecified
        TypeDecorator.__init__(self, **kwargs)

    def process_bind_param(self, value, dialect):
        if value is not None:
            try:
                assert self.allow_unspecified or int(value) in self.choices
            except:
                raise ValueError('{!r} not a valid option out of {}'.format(value, self.choices))
            else:
                return int(value)


class MultiChoice(TypeDecorator):
    """
    Utility class for storing the results of a group of checkboxes.  Each value
    is represented by an integer, so we store them as a comma-separated string.
    This can be marginally more convenient than a many-to-many table.  Like the
    Choice class, this takes an array of tuples of integers and strings.
    """
    impl = UnicodeText

    def __init__(self, choices, **kwargs):
        self.choices = choices
        TypeDecorator.__init__(self, **kwargs)

    def process_bind_param(self, value, dialect):
        return value if isinstance(value, str) else ','.join(value)

@declarative_base
class MainModel:
    id = Column(UUID, primary_key=True, default=lambda: str(uuid4()))

    required = ()

    def __init__(self, *args, **kwargs):
        if '_model' in kwargs:
            assert kwargs.pop('_model') == self.__class__.__name__
        default_constructor(self, *args, **kwargs)
        for attr, col in self.__table__.columns.items():
            if col.default:
                self.__dict__.setdefault(attr, col.default.execute())

    @property
    def _class_attrs(self):
        return {name: getattr(self.__class__, name) for name in dir(self.__class__)}

    def _invoke_adjustment_callbacks(self, label):
        callbacks = []
        for name, attr in self._class_attrs.items():
            if hasattr(attr, '__call__') and hasattr(attr, label):
                callbacks.append(getattr(self, name))
        callbacks.sort(key=lambda f: getattr(f, label))
        for func in callbacks:
            func()

    def presave_adjustments(self):
        self._invoke_adjustment_callbacks('presave_adjustment')

    def predelete_adjustments(self):
        self._invoke_adjustment_callbacks('predelete_adjustment')

    @property
    def cost_property_names(self):
        """Returns the names of all cost properties on this model."""
        return [name for name, attr in self._class_attrs.items() if isinstance(attr, cost_property)]

    @property
    def default_cost(self):
        """
        Returns the sum of all @cost_property values for this model instance.
        Because things like discounts exist, we ensure cost can never be negative.
        """
        return max(0, sum([getattr(self, name) for name in self.cost_property_names], 0))

    @class_property
    def unrestricted(cls):
        """
        Returns a set of column names which are allowed to be set by non-admin
        attendees filling out one of the registration forms.
        """
        return {col.name for col in cls.__table__.columns if not getattr(col, 'admin_only', True)}

    @class_property
    def all_bools(cls):
        """Returns the set of Boolean column names for this table."""
        return {col.name for col in cls.__table__.columns if isinstance(col.type, Boolean)}

    @class_property
    def all_checkgroups(cls):
        """Returns the set of MultiChoice column names for this table."""
        return {col.name for col in cls.__table__.columns if isinstance(col.type, MultiChoice)}

    @class_property
    def regform_bools(cls):
        """Returns the set of non-admin-only Boolean columns for this table."""
        return {colname for colname in cls.all_bools if colname in cls.unrestricted}

    @class_property
    def regform_checkgroups(cls):
        """Returns the set of non-admin-only MultiChoice columns for this table."""
        return {colname for colname in cls.all_checkgroups if colname in cls.unrestricted}

    @property
    def session(self):
        """
        Returns the session object which this model instance is attached to, or
        None if this instance is not attached to a session.
        """
        return Session.session_factory.object_session(self)

    @classmethod
    def get_field(cls, name):
        """Returns the column object with the provided name for this model."""
        return cls.__table__.columns[name]

    def __eq__(self, m):
        return self.id is not None and isinstance(m, MainModel) and self.id == m.id

    def __ne__(self, m):        # Python is stupid for making me do this
        return not (self == m)

    def __hash__(self):
        return hash(self.id)

    @property
    def is_new(self):
        """
        Boolean property indicating whether or not this instance has already
        been saved to the database or if it's a new instance which has never
        been saved and thus has no corresponding row in its database table.
        """
        return not instance_state(self).persistent

    @property
    def created(self):
        return self.get_tracking_by_instance(self, action=c.CREATED, last_only=True)

    @property
    def last_updated(self):
        return self.get_tracking_by_instance(self, action=c.UPDATED, last_only=True)

    @property
    def db_id(self):
        """
        A common convention in our forms is to pass an "id" parameter of "None"
        for new objects and to pass the actual id for objects which already
        exist in our database, which lets the backend know whether to perform a
        save or an update.  This method returns "None" for new objects and the
        id for existing objects, for use in such forms.
        """
        return None if self.is_new else self.id

    def orig_value_of(self, name):
        """
        Sometimes we mutate a model instance but then want to get the original
        value of a column before we changed it before we perform a save.  This
        method returns the original value (i.e. the value currently in the db)
        for the column whose name is provided.  If the value has not changed,
        this just returns the current value of that field.
        """
        hist = get_history(self, name)
        return (hist.deleted or hist.unchanged or [getattr(self, name)])[0]

    @suffix_property
    def _ints(self, name, val):
        choices = dict(self.get_field(name).type.choices)
        return [int(i) for i in str(val).split(',') if int(i) in choices] if val else []

    @suffix_property
    def _label(self, name, val):
        if not val or not name:
            return ''

        try:
            val = int(val)
        except ValueError:
            log.debug('{} is not an int, did we forget to migrate data for {} during a DB migration?').format(val, name)
            return ''

        label = self.get_field(name).type.choices.get(val)
        if not label:
            log.debug('{} does not have a label for {}, check your enum generating code').format(name, val)
        return label

    @suffix_property
    def _local(self, name, val):
        return val.astimezone(c.EVENT_TIMEZONE)

    @suffix_property
    def _labels(self, name, val):
        ints = getattr(self, name + '_ints')
        labels = dict(self.get_field(name).type.choices)
        return sorted(labels[i] for i in ints)

    def __getattr__(self, name):
        suffixed = suffix_property.check(self, name)
        if suffixed is not None:
            return suffixed

        try:
            [multi] = [col for col in self.__table__.columns if isinstance(col.type, MultiChoice)]
            choice = getattr(c, name)
            assert choice in [val for val, desc in multi.type.choices]
        except:
            pass
        else:
            return choice in getattr(self, multi.name + '_ints')

        if name.startswith('is_'):
            return self.__class__.__name__.lower() == name[3:]

        raise AttributeError(self.__class__.__name__ + '.' + name)

    def get_tracking_by_instance(self, instance, action, last_only=True):
        query = self.session.query(Tracking).filter_by(fk_id=instance.id, action=action).order_by(Tracking.when.desc())
        return query.first() if last_only else query.all()

    def apply(self, params, *, bools=(), checkgroups=(), restricted=True, ignore_csrf=True):
        """
        Args:
            restricted (bool): if true, restrict any changes only to fields which we allow attendees to set on their own
                if false, allow changes to any fields.
        """
        bools = self.regform_bools if restricted else bools
        checkgroups = self.regform_checkgroups if restricted else checkgroups
        for column in self.__table__.columns:
            if (not restricted or column.name in self.unrestricted) and column.name in params and column.name != 'id':
                if isinstance(params[column.name], list):
                    value = ','.join(map(str, params[column.name]))
                elif isinstance(params[column.name], bool):
                    value = params[column.name]
                else:
                    value = str(params[column.name]).strip()

                try:
                    if isinstance(column.type, Float):
                        value = float(value)
                    elif isinstance(column.type, Choice) and value == '':
                        value = None
                    elif isinstance(column.type, (Choice, Integer)):
                        value = int(float(value))
                    elif isinstance(column.type, UTCDateTime):
                        value = c.EVENT_TIMEZONE.localize(datetime.strptime(value, c.TIMESTAMP_FORMAT))
                    elif isinstance(column.type, Date):
                        value = datetime.strptime(value, c.DATE_FORMAT).date()
                except:
                    pass

                setattr(self, column.name, value)

        if cherrypy.request.method.upper() == 'POST':
            for column in self.__table__.columns:
                if column.name in bools:
                    setattr(self, column.name, column.name in params and bool(int(params[column.name])))
                elif column.name in checkgroups and column.name not in params:
                    setattr(self, column.name, '')

            if not ignore_csrf:
                check_csrf(params.get('csrf_token'))

class Session(SessionManager):
    engine = sqlalchemy.create_engine(c.SQLALCHEMY_URL, pool_size=50, max_overflow=100)

    @classmethod
    def initialize_db(cls, modify_tables=False, drop=False):
        """
        Initialize the database and optionally create/drop tables

        Initializes the database connection for use, and attempt to create any
        tables registered in our metadata which do not actually exist yet in the
        database.

        This calls the underlying sideboard function, HOWEVER, in order to actually create
        any tables, you must specify modify_tables=True.  The reason is, we need to wait for
        all models from all plugins to insert their mixin data, so we wait until one spot
        in order to create the database tables.

        Any calls to initialize_db() that do not specify modify_tables=True are ignored.
        i.e. anywhere in Sideboard that calls initialize_db() will be ignored
        i.e. ubersystem is forcing all calls that don't specify modify_tables=True to be ignored

        Keyword Arguments:
        modify_tables -- If False, this function does nothing.
        drop -- USE WITH CAUTION: If True, then we will drop any tables in the database
        """
        if modify_tables:
            super(Session, cls).initialize_db(drop=drop)

    class QuerySubclass(Query):
        @property
        def is_single_table_query(self):
            return len(self.column_descriptions) == 1

        @property
        def model(self):
            assert self.is_single_table_query, 'actions such as .order() and .icontains() and .iexact() are only valid for single-table queries'
            return self.column_descriptions[0]['type']

        def order(self, attrs):
            order = []
            for attr in listify(attrs):
                col = getattr(self.model, attr.lstrip('-'))
                order.append(col.desc() if attr.startswith('-') else col)
            return self.order_by(*order)

        def icontains(self, attr=None, val=None, **filters):
            query = self
            if len(self.column_descriptions) == 1 and filters:
                for colname, val in filters.items():
                    query = query.filter(getattr(self.model, colname).ilike('%{}%'.format(val)))
            if attr and val:
                query = self.filter(attr.ilike('%{}%'.format(val)))
            return query

        def iexact(self, **filters):
            return self.filter(*[func.lower(getattr(self.model, attr)) == func.lower(val) for attr, val in filters.items()])

    class SessionMixin:
        def admin_user(self):
            return self.admin_account(cherrypy.session['account_id']).user

        def logged_in_user(self):
            return self.user(cherrypy.session['user_id'])

        def get_account_by_email(self, email):
            return self.query(AdminAccount).join(User).filter(func.lower(User.email) == func.lower(email)).one()

        def no_email(self, subject):
            return not self.query(Email).filter_by(subject=subject).all()

        def verified_users(self):
            return self.query(User).filter(User.verificatio_status != c.INVALID_STATUS)

        def search(self, text, *filters):
            users = self.query(User).filter(*filters)
            if ':' in text:
                target, term = text.split(':', 1)
                if target == 'email':
                    return users.icontains(User.normalized_email, User.normalize_email(term))

            terms = text.split()
            if len(terms) == 2:
                first, last = terms
                if first.endswith(','):
                    last, first = first.strip(','), last
                name_cond = users.icontains_condition(first_name=first, last_name=last)
                legal_name_cond = users.icontains_condition(legal_name="{}%{}".format(first, last))
                return users.filter(or_(name_cond, legal_name_cond))
            elif len(terms) == 1 and terms[0].endswith(','):
                last = terms[0].rstrip(',')
                name_cond = users.icontains_condition(last_name=last)
                # Known issue: search may include first name if legal name is set
                legal_name_cond = users.icontains_condition(legal_name=last)
                return users.filter(or_(name_cond, legal_name_cond))
            elif len(terms) == 1 and terms[0].isdigit():
                if len(terms[0]) == 10:
                    return users.filter(or_(User.ec_phone == terms[0], User.cellphone == terms[0]))
            elif len(terms) == 1 and re.match('^[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12}$', terms[0]):
                return users.filter(or_(User.id == terms[0], User.public_id == terms[0]))

            checks = []
            for attr in ['first_name', 'last_name',  'email', 'comments', 'admin_notes']:
                checks.append(getattr(User, attr).ilike('%' + text + '%'))
            return users.filter(or_(*checks))

        def insert_test_admin_account(self):
            """
            insert a test admin into the database with username "magfest@example.com" password "magfest"
            this is ONLY allowed if no other admins already exist in the database.
            :return: True if success, False if failure
            """
            if self.query(sa.AdminAccount).count() != 0:
                return False

            user = sa.User(
                verified=True,
                first_name='Test',
                last_name='Developer',
                email='admin@example.com',
            )
            self.add(user)

            self.add(sa.AdminAccount(
                user_id=user.id,
                access=','.join(str(level) for level, name in c.ACCESS_OPTS),
                hashed=bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt())
            ))

            return True

    @classmethod
    def model_mixin(cls, model):
        if model.__name__ in ['SessionMixin', 'QuerySubclass']:
            target = getattr(cls, model.__name__)
        else:
            for target in cls.all_models():
                if target.__name__ == model.__name__:
                    break
            else:
                raise ValueError('No existing model with name {}'.format(model.__name__))

        for name in dir(model):
            if not name.startswith('_'):
                attr = getattr(model, name)
                if hasattr('target', '__table__') and name in target.__table__.c:
                    attr.key = attr.key or name
                    attr.name = attr.name or name
                    attr.table = target.__table__
                    target.__table__.c.replace(attr)
                else:
                    setattr(target, name, attr)
        return target

class User(MainModel):
    watchlist_id = Column(UUID, ForeignKey('watch_list.id', ondelete='set null'), nullable=True, default=None)

    verified   = Column(Boolean, default=False, admin_only=True)
    first_name    = Column(UnicodeText)
    last_name     = Column(UnicodeText)
    email         = Column(UnicodeText)
    birthdate     = Column(Date, nullable=True, default=None)

    no_cellphone  = Column(Boolean, default=False)
    cellphone     = Column(UnicodeText)

    found_how   = Column(UnicodeText)
    comments    = Column(UnicodeText)
    admin_notes = Column(UnicodeText, admin_only=True)

    admin_account     = relationship('AdminAccount', backref=backref('user', load_on_pending=True), uselist=False)

    _repr_attr_names = ['full_name']

    @presave_adjustment
    def _misc_adjustments(self):
        if self.birthdate == '':
            self.birthdate = None

        if self.birthdate:
            self.age_group = self.age_group_conf['val']

        for attr in ['first_name', 'last_name']:
            value = getattr(self, attr)
            if value.isupper() or value.islower():
                setattr(self, attr, value.title())

    @property
    def age_group_conf(self):
        if self.birthdate:
            day = sa.localized_now().date()
            user_age = (day - self.birthdate).days // 365.2425
            for val, age_group in c.AGE_GROUP_CONFIGS.items():
                if val != c.AGE_UNKNOWN and age_group['min_age'] <= user_age <= age_group['max_age']:
                    return age_group

        return c.AGE_GROUP_CONFIGS[int(self.age_group or c.AGE_UNKNOWN)]

    @hybrid_property
    def full_name(self):
        return '{self.first_name} {self.last_name}'.format(self=self)

    @full_name.expression
    def full_name(cls):
        return case([
            (or_(cls.first_name == None, cls.first_name == ''), 'zzz')
        ], else_=func.lower(cls.first_name + ' ' + cls.last_name))

    @hybrid_property
    def last_first(self):
        return '{self.last_name}, {self.first_name}'.format(self=self)

    @last_first.expression
    def last_first(cls):
        return case([
            (or_(cls.first_name == None, cls.first_name == ''), 'zzz')
        ], else_=func.lower(cls.last_name + ', ' + cls.first_name))


    @property
    def watchlist_guess(self):
        try:
            with Session() as session:
                return [w.to_dict() for w in session.guess_attendee_watchentry(self)]
        except:
            return None

    @property
    def banned(self):
        return listify(self.watch_list or self.watchlist_guess)

    @property
    def age(self):
        if self.birthdate:
            date = sa.localized_now().date()
            return (date - self.birthdate).days // 365.2425
        else:
            return 0

class WatchList(MainModel):
    first_names     = Column(UnicodeText)
    last_name       = Column(UnicodeText)
    email           = Column(UnicodeText, default='')
    birthdate       = Column(Date, nullable=True, default=None)
    reason          = Column(UnicodeText)
    action          = Column(UnicodeText)
    active          = Column(Boolean, default=True)
    users = relationship('User', backref=backref('watch_list', load_on_pending=True))

    @presave_adjustment
    def _fix_birthdate(self):
        if self.birthdate == '':
            self.birthdate = None


class AdminAccount(MainModel):
    user_id = Column(UUID, ForeignKey('user.id'), unique=True)
    hashed      = Column(UnicodeText)
    access      = Column(MultiChoice(c.ACCESS_OPTS))

    password_reset = relationship('PasswordReset', backref='admin_account', uselist=False)

    def __repr__(self):
        return '<{}>'.format(self.user.full_name)

    @staticmethod
    def admin_name():
        try:
            with Session() as session:
                return session.admin_user().full_name
        except:
            return None

    @staticmethod
    def admin_email():
        try:
            with Session() as session:
                return session.admin_user().email
        except:
            return None

    @staticmethod
    def access_set(id=None):
        try:
            with Session() as session:
                id = id or cherrypy.session['account_id']
                return set(session.admin_account(id).access_ints)
        except:
            return set()


class PasswordReset(MainModel):
    account_id = Column(UUID, ForeignKey('admin_account.id'), unique=True)
    generated  = Column(UTCDateTime, server_default=utcnow())
    hashed     = Column(UnicodeText)

    @property
    def is_expired(self):
        return self.generated < datetime.now(UTC) - timedelta(days=7)

class ApprovedEmail(MainModel):
    ident = Column('subject', UnicodeText)  # TODO: rename column to "ident" in the database; will require a db migration

    _repr_attr_names = ['ident']


class Email(MainModel):
    fk_id   = Column(UUID, nullable=True)
    ident   = Column(UnicodeText)
    model   = Column(UnicodeText)
    when    = Column(UTCDateTime, default=lambda: datetime.now(UTC))
    subject = Column(UnicodeText)
    dest    = Column(UnicodeText)
    body    = Column(UnicodeText)

    _repr_attr_names = ['subject']

    @cached_property
    def fk(self):
        try:
            return getattr(self.session, globals()[self.model].__tablename__)(self.fk_id)
        except:
            return None

    @property
    def rcpt_name(self):
        if self.model == 'Group':
            return self.fk.leader.full_name
        else:
            return self.fk.full_name

    @property
    def is_html(self):
        return '<body' in self.body

    @property
    def html(self):
        if self.is_html:
            return SafeString(re.split('<body[^>]*>', self.body)[1].split('</body>')[0])
        else:
            return SafeString(self.body.replace('\n', '<br/>'))


class Tracking(MainModel):
    fk_id  = Column(UUID)
    model  = Column(UnicodeText)
    when   = Column(UTCDateTime, default=lambda: datetime.now(UTC))
    who    = Column(UnicodeText)
    which  = Column(UnicodeText)
    links  = Column(UnicodeText)
    action = Column(Choice(c.TRACKING_OPTS))
    data   = Column(UnicodeText)

    @classmethod
    def format(cls, values):
        return ', '.join('{}={}'.format(k, v) for k, v in values.items())

    @classmethod
    def repr(cls, column, value):
        try:
            s = repr(value)
            if column.name == 'hashed':
                return '<bcrypted>'
            elif isinstance(column.type, MultiChoice):
                opts = dict(column.type.choices)
                return repr('' if not value else (','.join(opts[int(opt)] for opt in value.split(',') if int(opt or 0) in opts)))
            elif isinstance(column.type, Choice) and value not in [None, '']:
                return repr(dict(column.type.choices).get(int(value), '<nonstandard>'))
            else:
                return s
        except Exception as e:
            raise ValueError('error formatting {} ({!r})'.format(column.name, value)) from e

    @classmethod
    def differences(cls, instance):
        diff = {}
        for attr, column in instance.__table__.columns.items():
            new_val = getattr(instance, attr)
            old_val = instance.orig_value_of(attr)
            if old_val != new_val:
                """
                important note: here we try and show the old vs new value for something that has been changed
                so that we can report it in the tracking page.

                Sometimes, however, if we changed the type of the value in the database (via a database migration)
                the old value might not be able to be shown as the new type (i.e. it used to be a string, now it's int).
                In that case, we won't be able to show a representation of the old value and instead we'll log it as
                '<ERROR>'.  In theory the database migration SHOULD be the thing handling this, but if it doesn't, it
                becomes our problem to deal with.

                We are overly paranoid with exception handling here because the tracking code should be made to
                never, ever, ever crash, even if it encounters insane/old data that really shouldn't be our problem.
                """
                try:
                    old_val_repr = cls.repr(column, old_val)
                except Exception as e:
                    log.error("tracking repr({}) failed on old value".format(attr), exc_info=True)
                    old_val_repr = "<ERROR>"

                try:
                    new_val_repr = cls.repr(column, new_val)
                except Exception as e:
                    log.error("tracking repr({}) failed on new value".format(attr), exc_info=True)
                    new_val_repr = "<ERROR>"

                diff[attr] = "'{} -> {}'".format(old_val_repr, new_val_repr)
        return diff

    # TODO: add new table for page views to eliminated track_pageview method and to eliminate Budget special case
    @classmethod
    def track(cls, action, instance):
        if action in [c.CREATED]:
            vals = {attr: cls.repr(column, getattr(instance, attr)) for attr, column in instance.__table__.columns.items()}
            data = cls.format(vals)
        elif action == c.UPDATED:
            diff = cls.differences(instance)
            data = cls.format(diff)
            if len(diff) == 1 and 'badge_num' in diff:
                action = c.AUTO_BADGE_SHIFT
            elif not data:
                return
        else:
            data = 'id={}'.format(instance.id)
        links = ', '.join(
            '{}({})'.format(list(column.foreign_keys)[0].column.table.name, getattr(instance, name))
            for name, column in instance.__table__.columns.items()
            if column.foreign_keys and getattr(instance, name)
        )
        who = AdminAccount.admin_name() or (current_thread().name if current_thread().daemon else 'non-admin')

        def _insert(session):
            session.add(Tracking(
                model=instance.__class__.__name__,
                fk_id=instance.id,
                which=repr(instance),
                who=who,
                links=links,
                action=action,
                data=data
            ))
        if instance.session:
            _insert(instance.session)
        else:
            with Session() as session:
                _insert(session)

    @classmethod
    def track_pageview(cls, url, query):
        # Track any views of the budget pages
        if "budget" in url:
            Tracking.track(c.PAGE_VIEWED, "Budget")
        else:
            # Only log the page view if there's a valid attendee ID
            params = dict(parse_qsl(query))
            if 'id' not in params or params['id'] == 'None':
                return


Tracking.UNTRACKED = [Tracking, Email]


def _make_getter(model):
    def getter(self, params=None, *, bools=(), checkgroups=(), allowed=(), restricted=False, ignore_csrf=False, **query):
        if query:
            return self.query(model).filter_by(**query).one()
        elif isinstance(params, str):
            return self.query(model).filter_by(id=params).one()
        else:
            params = params.copy()
            id = params.pop('id', 'None')
            if id == 'None':
                inst = model()
            else:
                inst = self.query(model).filter_by(id=id).one()

            if not ignore_csrf:
                assert not {k for k in params if k not in allowed} or cherrypy.request.method == 'POST', 'POST required'
            inst.apply(params, bools=bools, checkgroups=checkgroups, restricted=restricted, ignore_csrf=ignore_csrf)
            return inst
    return getter

@swallow_exceptions
def _presave_adjustments(session, context, instances='deprecated'):
    """
    precondition: c.BADGE_LOCK is acquired already.
    """
    for model in chain(session.dirty, session.new):
        model.presave_adjustments()
    for model in session.deleted:
        model.predelete_adjustments()

@swallow_exceptions
def _track_changes(session, context, instances='deprecated'):
    for action, instances in {c.CREATED: session.new, c.UPDATED: session.dirty, c.DELETED: session.deleted}.items():
        for instance in instances:
            if instance.__class__ not in Tracking.UNTRACKED:
                Tracking.track(action, instance)

def register_session_listeners():
    """
    NOTE 1: IMPORTANT!!! Because we are locking our c.BADGE_LOCK at the start of this, all of these functions MUST NOT
    THROW ANY EXCEPTIONS.  If they do throw exceptions, the chain of hooks will not be completed, and the lock won't
    be released, resulting in a deadlock and heinous, horrible, and hard to debug server lockup.

    You MUST use the @swallow_exceptions decorator on ALL functions
    between _acquire_badge_lock and _release_badge_lock in order to prevent them from throwing exceptions.

    NOTE 2: The order in which we register these listeners matters.
    """
    listen(Session.session_factory, 'before_flush', _presave_adjustments)
    listen(Session.session_factory, 'before_flush', _track_changes)
register_session_listeners()


def initialize_db():
    """
    Initialize the database on startup

    We want to do this only after all other plugins have had a chance to initialize
    and add their 'mixin' data (i.e. extra colums) into the models.

    Also, it's possible that the DB is still initializing and isn't ready to accept connections, so,
    if this fails, keep trying until we're able to connect.

    This should be the ONLY spot (except for maintenance tools) in all of core ubersystem or any plugins
    that attempts to create tables by passing modify_tables=True to Session.initialize_db()
    """
    for _model in Session.all_models():
        setattr(Session.SessionMixin, _model.__tablename__, _make_getter(_model))

    num_tries_remaining = 10
    while not stopped.is_set():
        try:
            Session.initialize_db(modify_tables=True)
        except KeyboardInterrupt:
            log.critical('DB initialize: Someone hit Ctrl+C while we were starting up')
        except:
            num_tries_remaining -= 1
            if num_tries_remaining == 0:
                log.error("DB initialize: couldn't connect to DB, we're giving up")
                raise
            log.error("DB initialize: can't connect to / initialize DB, will try again in 5 seconds", exc_info=True)
            stopped.wait(5)
        else:
            break

on_startup(initialize_db, priority=1)