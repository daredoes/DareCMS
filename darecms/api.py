from darecms.common import *

__version__ = 'v0.1'

config_fields = [
    'EVENT_NAME',
    'ORGANIZATION_NAME',
    'YEAR',
    'EPOCH',

    'EVENT_VENUE',
    'EVENT_VENUE_ADDRESS',

    'AT_THE_CON',
    'POST_CON',

]


class ConfigLookup:
    def info(self):
        output = {
            'API_VERSION': __version__
        }
        for field in config_fields:
            output[field] = getattr(c, field)
        return output

    def lookup(self, field):
        if field.upper() in config_fields:
            return getattr(c, field.upper())

services.register(ConfigLookup(), 'config')
