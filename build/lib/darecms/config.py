from darecms.common import *


class _Overridable:
    "Base class we extend below to allow plugins to add/override config options."
    @classmethod
    def mixin(cls, klass):
        for attr in dir(klass):
            if not attr.startswith('_'):
                setattr(cls, attr, getattr(klass, attr))
        return cls

    def include_plugin_config(self, plugin_config):
        """Plugins call this method to merge their own config into the global c object."""

        for attr, val in plugin_config.items():
            if not isinstance(val, dict):
                setattr(self, attr.upper(), val)

        if 'enums' in plugin_config:
            self.make_enums(plugin_config['enums'])

        if 'dates' in plugin_config:
            self.make_dates(plugin_config['dates'])

    def make_dates(self, config_section):
        """
        Plugins can define a [dates] section in their config to create their
        own deadlines on the global c object.  This method is called automatically
        by c.include_plugin_config() if a "[dates]" section exists.
        """
        for _opt, _val in config_section.items():
            if not _val:
                _dt = None
            elif ' ' in _val:
                _dt = self.EVENT_TIMEZONE.localize(datetime.strptime(_val, '%Y-%m-%d %H'))
            else:
                _dt = self.EVENT_TIMEZONE.localize(datetime.strptime(_val + ' 23:59', '%Y-%m-%d %H:%M'))
            setattr(self, _opt.upper(), _dt)
            if _dt:
                self.DATES[_opt.upper()] = _dt

    def make_enums(self, config_section):
        """
        Plugins can define an [enums] section in their config to create their
        own enums on the global c object.  This method is called automatically
        by c.include_plugin_config() if an "[enums]" section exists.
        """
        for name, subsection in config_section.items():
            c.make_enum(name, subsection)

    def make_enum(self, enum_name, section, prices=False):
        """
        Plugins can call this to define individual enums, or call the make_enums
        function to make all enums defined there.  See the [enums] section in
        configspec.ini file, which explains what fields are added to the global
        c object for each enum.
        """
        opts, lookup, varnames = [], {}, []
        for name, desc in section.items():
            if isinstance(desc, int):
                val, desc = desc, name
            else:
                varnames.append(name.upper())
                val = self.create_enum_val(name)

            if desc:
                opts.append((val, desc))
                if prices:
                    lookup[desc] = val
                else:
                    lookup[val] = desc

        enum_name = enum_name.upper()
        setattr(self, enum_name + '_OPTS', opts)
        setattr(self, enum_name + '_VARS', varnames)
        setattr(self, enum_name + ('' if enum_name.endswith('S') else 'S'), lookup)

    def create_enum_val(self, name):
        val = int(sha512(name.upper().encode()).hexdigest()[:7], 16)
        setattr(self, name.upper(), val)
        return val


class Config(_Overridable):
    """
    We have two types of configuration.  One is the values which come directly from our config file, such
    as the name of our event.  The other is things which depend on the date/time (such as the badge price,
    which can change over time), or whether we've hit our configured attendance cap (which changes based
    on the state of the database).  See the comments in configspec.ini for explanations of the particilar
    options, which are documented there.

    This class has a single global instance called "c" which contains values of either type of config, e.g.
    if you need to check whether dealer registration is open in your code, you'd say c.DEALER_REG_OPEN
    For all of the datetime config options, we also define BEFORE_ and AFTER_ properties, e.g. you can
    check the booleans returned by c.BEFORE_PLACEHOLDER_DEADLINE or c.AFTER_PLACEHOLDER_DEADLINE
    """

    @property
    def CSRF_TOKEN(self):
        return cherrypy.session['csrf_token'] if 'csrf_token' in cherrypy.session else ''

    @property
    def PAGE_PATH(self):
        return cherrypy.request.path_info

    @property
    def PAGE(self):
        return cherrypy.request.path_info.split('/')[-1]

    @request_cached_property
    def CURRENT_ADMIN(self):
        try:
            with sa.Session() as session:
                return session.admin_user().to_dict()
        except Exception as e:
            print(e)
            return {}

    @property
    def HTTP_METHOD(self):
        return cherrypy.request.method

    @request_cached_property
    def ADMIN_ACCESS_SET(self):
        return sa.AdminAccount.access_set()

    def __getattr__(self, name):
        if name.split('_')[0] in ['BEFORE', 'AFTER']:
            date_setting = getattr(c, name.split('_', 1)[1])
            if not date_setting:
                return False
            elif name.startswith('BEFORE_'):
                return sa.localized_now() < date_setting
            else:
                return sa.localized_now() > date_setting
        elif name.startswith('HAS_') and name.endswith('_ACCESS'):
            return getattr(c, '_'.join(name.split('_')[1:-1])) in c.ADMIN_ACCESS_SET
        elif name.endswith('_COUNT'):
            item_check = name.rsplit('_', 1)[0]
            badge_type = getattr(self, item_check, None)
            return self.get_badge_count_by_type(badge_type) if badge_type else None
        elif name.endswith('_AVAILABLE'):
            item_check = name.rsplit('_', 1)[0]
            stock_setting = getattr(self, item_check + '_STOCK', None)
            count_check = getattr(self, item_check + '_COUNT', None)
            if count_check is None:
                return False  # Things with no count are never considered available
            elif stock_setting is None:
                return True  # Defaults to unlimited stock for any stock not configured
            else:
                return int(count_check) < int(stock_setting)
        elif hasattr(_secret, name):
            return getattr(_secret, name)
        elif name.lower() in _config:
            return _config[name.lower()]
        elif name.lower() in _config['secret']:
            return _config['secret'][name.lower()]
        else:
            raise AttributeError('no such attribute {}'.format(name))


class SecretConfig(_Overridable):
    """
    This class is for properties which we don't want to be used as Javascript
    variables.  Properties on this class can be accessed normally through the
    global c object as if they were defined there.
    """

    @property
    def SQLALCHEMY_URL(self):
        """
        support reading the DB connection info from an environment var (used with Docker containers)
        DB_CONNECTION_STRING should contain the full Postgres URI
        """
        db_connection_string = os.environ.get('DB_CONNECTION_STRING')

        if db_connection_string is not None:
            return db_connection_string
        else:
            return _config['secret']['sqlalchemy_url']

c = Config()
_secret = SecretConfig()

_config = parse_config(__file__)  # outside this module, we use the above c global instead of using this directly


def _unrepr(d):
    for opt in d:
        val = d[opt]
        if val in ['True', 'False']:
            d[opt] = ast.literal_eval(val)
        elif isinstance(val, str) and val.isdigit():
            d[opt] = int(val)
        elif isinstance(d[opt], dict):
            _unrepr(d[opt])

_unrepr(_config['appconf'])
c.APPCONF = _config['appconf'].dict()

c.DATES = {}
c.TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'
c.DATE_FORMAT = '%Y-%m-%d'
c.EVENT_TIMEZONE = pytz.timezone(c.EVENT_TIMEZONE)

c.make_dates(_config['dates'])


def _is_intstr(s):
    if s and s[0] in ('-', '+'):
        return s[1:].isdigit()
    return s.isdigit()


# Under certain conditions, we want to completely remove certain payment options from the system.
# However, doing so cleanly also risks an exception being raised if these options are referenced elsewhere in the code
# (i.e., c.STRIPE). So we create an enum val to allow code to check for these variables without exceptions.
c.make_enums(_config['enums'])

for _name, _val in _config['integer_enums'].items():
    if isinstance(_val, int):
        setattr(c, _name.upper(), _val)

for _name, _section in _config['integer_enums'].items():
    if isinstance(_section, dict):
        _interpolated = OrderedDict()
        for _desc, _val in _section.items():
            if _is_intstr(_val):
                _price = int(_val)
            else:
                _price = getattr(c, _val.upper())

            _interpolated[_desc] = _price

        c.make_enum(_name, _interpolated, prices=_name.endswith('_price'))

# plugins can use this to append paths which will be included as <script> tags, e.g. if a plugin
# appends '../static/foo.js' to this list, that adds <script src="../static/foo.js"></script> to
# all of the pages on the site except for preregistration pages (for performance)
c.JAVASCRIPT_INCLUDES = []
