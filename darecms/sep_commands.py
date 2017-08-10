from glob import glob
from os.path import exists, join
from darecms.common import *


@entry_point
def alembic(*args):
    """
    Frontend for alembic script with additional uber specific facilities.

    "sep alembic" supports all the same arguments as the regular "alembic"
    command, with the addition of the "--plugin PLUGIN_NAME" option.

    Passing "--plugin PLUGIN_NAME" will choose the correct alembic version path
    for the given plugin. If "--plugin" is omitted, it will default to "uber".

    If "--version-path PATH" is also specified, it will override the version
    path chosen for the plugin. This functionality is rarely needed, and best
    left unused.

    If a new migration revision is created for a plugin that previously did
    not have any revisions, then a new branch label is applied using the
    plugin name. For example::

        sep alembic --plugin new_plugin revision --autogenerate -m "Initial migration"

    A new revision script will be created in "new_plugin/alembic/versions/"
    with a branch label of "new_plugin". The "new_plugin/alembic/versions/"
    directory will be created if it does not already exist.
    """
    from alembic.config import CommandLine
    from sideboard.config import config as sideboard_config
    from sideboard.internal.imports import plugin_dirs
    from darecms.migration import create_alembic_config, \
        get_plugin_head_revision, version_locations

    argv = args if args else sys.argv[1:]

    # Extract the "--plugin" option from argv.
    plugin_name = 'darecms'
    for plugin_opt in ('-p', '--plugin'):
        if plugin_opt in argv:
            plugin_index = argv.index(plugin_opt)
            argv.pop(plugin_index)
            plugin_name = argv.pop(plugin_index)

    assert plugin_name in version_locations, (
        'Plugin "{}" does not exist in {}'.format(
            plugin_name, sideboard_config['plugins_dir']))

    commandline = CommandLine(prog='sep alembic')
    if {'-h', '--help'}.intersection(argv):
        # If "--help" is passed, add a description of the "--plugin" option
        commandline.parser.add_argument(
            '-p', '--plugin',
            type=str,
            default='darecms',
            help='Name of plugin in which to add new versions')

    options = commandline.parser.parse_args(argv)

    if not hasattr(options, 'cmd'):
        commandline.parser.error('too few arguments')

    kwarg_names = options.cmd[2]
    if 'version_path' in kwarg_names and not options.version_path:
        # If the command supports the "--version-path" option and it was not
        # specified, default to the version path of the given plugin.
        options.version_path = version_locations[plugin_name]

        if 'branch_label' in kwarg_names and options.version_path and \
                not glob(join(options.version_path, '*.py')):
            # If the command supports the "--branch-label" option and there
            # aren't any existing revisions, then always apply the plugin
            # name as the branch label.
            options.branch_label = plugin_name

    if 'head' in kwarg_names and not options.head and \
            options.branch_label != plugin_name:
        # If the command supports the "--head" option and it was not specified
        # and the we're not creating a new branch for the plugin, then make
        # this revision on top of the plugin's branch head.
        revision = get_plugin_head_revision(plugin_name)
        options.head = revision.revision
        if revision.is_branch_point:
            options.splice = True

    commandline.run_cmd(create_alembic_config(cmd_opts=options), options)


@entry_point
def print_config():
    """
    print all config values to stdout, used for debugging / status checking
    useful if you want to verify that CMS has pulled in the INI values you think it has.
    """
    from darecms.config import _config
    pprint(_config.dict())


@entry_point
def insert_admin():
    with Session() as session:
        if session.insert_test_admin_account():
            print("Test admin account created successfully")
        else:
            print("Not allowed to create admin account at this time")


@entry_point
def drop_db():
    assert c.DEV_BOX, 'drop_uber_db is only available on development boxes'
    Session.initialize_db(modify_tables=False, drop=True)


@entry_point
def reset_db():
    assert c.DEV_BOX, 'reset_uber_db is only available on development boxes'
    Session.initialize_db(modify_tables=True, drop=True)
    insert_admin()
