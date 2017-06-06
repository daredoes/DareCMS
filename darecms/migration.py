from collections import OrderedDict
from os.path import abspath, dirname, join

from alembic import command
from alembic.config import Config as AlembicConfig
from alembic.script import ScriptDirectory

from sideboard.internal.imports import plugin_dirs


# Path to "alembic.ini", cached here for convenience
alembic_ini_path = abspath(join(plugin_dirs['uber'], 'alembic.ini'))

# Path to "alembic" directory, cached here for convenience
script_location = abspath(join(plugin_dirs['uber'], 'alembic'))

# Version locations are usually hard-coded in "alembic.ini". Since uber ships
# with a variety of plugins, each with its own set of version scripts, we must
# dynamically create the set of version locations.
#
# `sep alembic` uses the following convention for each version location:
#     PLUGIN_DIR/alembic/versions
version_locations = OrderedDict()
for name, path in plugin_dirs.items():
    version_locations[name] = join(path, 'alembic', 'versions')


# Version locations in the format expected in "alembic.ini", cached here for
# convenience
version_locations_option = ','.join(version_locations.values())


def create_alembic_config(**kwargs):
    """Returns an `alembic.config.Config` object configured for uber.
    """
    kwargs['file_'] = alembic_ini_path
    alembic_config = AlembicConfig(**kwargs)
    # Override settings from "alembic.ini"
    alembic_config.set_main_option('script_location', script_location)
    alembic_config.set_main_option(
        'version_locations', version_locations_option)
    return alembic_config


def get_plugin_head_revision(plugin_name):
    """Returns an `alembic.script.Revision` object for the given plugin's head.
    """
    alembic_config = create_alembic_config()
    script = ScriptDirectory.from_config(alembic_config)
    other_plugins = set(plugin_dirs.keys()).difference({plugin_name})

    def _get_plugin_head_revision(revision_text):
        revision = script.get_revision(revision_text)
        while not revision.is_branch_point and not revision.is_head:
            revision = script.get_revision(list(revision.nextrev)[0])

        if revision.is_head:
            return revision
        else:
            for next_revision_text in revision.nextrev:
                next_revision = script.get_revision(next_revision_text)
                if set(next_revision.branch_labels).isdisjoint(other_plugins):
                    return get_plugin_head_revision(next_revision.revision)
            return revision

    return _get_plugin_head_revision(plugin_name)


def stamp(version):
    """Stamp the "version_table" in the database with the given version.

    This is typically used after the database is created by some process other
    than alembic, and you'd like to stamp the database as being up-to-date by
    calling::

        from uber.migration import stamp
        stamp('heads')

    """
    from darecms.models import Session
    with Session.engine.begin() as connection:
        if version:
            alembic_config = create_alembic_config()
            alembic_config.attributes['connection'] = connection
            command.stamp(alembic_config, version)
        else:
            connection.execute('drop table if exists alembic_version;')
