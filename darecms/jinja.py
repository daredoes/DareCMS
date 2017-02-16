from darecms.common import *


class JinjaEnv:
    _env = None
    _exportable_functions = {}
    _filter_functions = {}
    _template_dirs = []

    @staticmethod
    def append_template_dir(dirname):
        """
        Add another template directory we should search when looking up templates.
        """
        JinjaEnv._template_dirs.insert(0, dirname)

    @staticmethod
    def env():
        if JinjaEnv._env is None:
            JinjaEnv._env = JinjaEnv._init_env()
        return JinjaEnv._env

    @staticmethod
    def _init_env():
        env = jinja2.Environment(
                # autoescape=_guess_autoescape,
                loader=jinja2.FileSystemLoader(JinjaEnv._template_dirs)
            )

        for name, func in JinjaEnv._exportable_functions.items():
            env.globals[name] = func

        for name, func in JinjaEnv._filter_functions.items():
            env.filters[name] = func

        return env

    @staticmethod
    def jinja_export(name=None):
        def wrap(func):
            JinjaEnv._exportable_functions[name if name else func.__name__] = func
            return func
        return wrap

    @staticmethod
    def jinja_filter(name=None):
        def wrap(func):
            JinjaEnv._filter_functions[name if name else func.__name__] = func
            return func
        return wrap


def template_overrides(dirname):
    """
    Each event can have its own plugin and override our default templates with
    its own by calling this method and passing its templates directory.
    """
    JinjaEnv.append_template_dir(dirname)

for directory in c.TEMPLATE_DIRS:
    template_overrides(directory)