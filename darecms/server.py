from darecms.common import *

mimetypes.init()


def _add_email():
    [body] = cherrypy.response.body
    body = body.replace(b'<body>', b'''<body>Please contact us via <a href="CONTACT_URL">CONTACT_URL</a> if you're not sure why you're seeing this page.'''.replace(b'CONTACT_URL', c.CONTACT_URL.encode('utf-8')))
    cherrypy.response.headers['Content-Length'] = len(body)
    cherrypy.response.body = [body]
cherrypy.tools.add_email_to_error_page = cherrypy.Tool('after_error_response', _add_email)


def log_exception_with_verbose_context(debug=False, msg=''):
    """
    Write the request headers, session params, page location, and the last error's traceback to the cherrypy error log.
    Do this all one line so all the information can be collected by external log collectors and easily displayed.
    """

    page_location = 'Request: ' + cherrypy.request.request_line

    admin_name = AdminAccount.admin_name()
    admin_txt = 'Current admin user is: {}'.format(admin_name if admin_name else '[non-admin user]')

    max_reporting_length = 1000   # truncate to reasonably large size in case they uploaded attachments

    p = ["  %s: %s" % (k, v[:max_reporting_length]) for k, v in cherrypy.request.params.items()]
    post_txt = 'Request Params:\n' + '\n'.join(p)

    session_txt = 'Session Params:\n' + pformat(cherrypy.session.items(), width=40)

    h = ["  %s: %s" % (k, v) for k, v in cherrypy.request.header_list]
    headers_txt = 'Request Headers:\n' + '\n'.join(h)

    full_msg = '\n'.join([msg, 'Exception encountered', page_location, admin_txt, post_txt, session_txt, headers_txt])
    log.error(full_msg, exc_info=True)
cherrypy.tools.custom_verbose_logger = cherrypy.Tool('before_error_response', log_exception_with_verbose_context)


class StaticViews:
    def path_args_to_string(self, path_args):
        return '/'.join(path_args)

    def get_full_path_from_path_args(self, path_args):
        return 'static_views/' + self.path_args_to_string(path_args)

    def get_filename_from_path_args(self, path_args):
        return path_args[-1]

    @cherrypy.expose
    def default(self, *path_args, **kwargs):
        content_filename = self.get_filename_from_path_args(path_args)

        template_name = self.get_full_path_from_path_args(path_args)
        try:
            content = render(template_name)
        except jinja2.exceptions.TemplateNotFound as e:
            raise cherrypy.HTTPError(404, "Couldn't find {}".format(template_name)) from e

        guessed_content_type = mimetypes.guess_type(content_filename)[0]
        return cherrypy.lib.static.serve_fileobj(content, name=content_filename, content_type=guessed_content_type)

@all_renderable()
class Root:
    def index(self):
        raise HTTPRedirect('common/')

    static_views = StaticViews()

mount_site_sections(c.MODULE_ROOT)

cherrypy.tree.mount(Root(), c.PATH, c.APPCONF)
static_overrides(join(c.MODULE_ROOT, 'static'))

# DaemonTask(SendAllAutomatedEmailsJob.send_all_emails, interval=300,   name="send emails")

# TODO: this should be replaced by something a little cleaner, but it can be a useful debugging tool
# DaemonTask(lambda: log.error(Session.engine.pool.status()), interval=5)
