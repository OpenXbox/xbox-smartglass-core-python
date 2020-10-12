from quart import current_app as app
from . import routes


@routes.route('/')
def index():
    routes = set([str(rule) for rule in app.url_map.iter_rules()])
    return app.success(endpoints=sorted(routes))
