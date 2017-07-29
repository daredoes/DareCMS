from darecms.common import *


@all_renderable()
class Root:

    def index(self):
        return {}

    def invalid(self, **params):
        return {
            'message': params.get('message')
        }

    def creative(self):
        return {}