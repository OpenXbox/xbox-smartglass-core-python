from flask import Blueprint
routes = Blueprint('routes', __name__)

from .index import *  # noqa: F401,F403
from .auth import *  # noqa: F401,F403
from .device import *  # noqa: F401,F403
from .web import *  # noqa: F401,F403
from .versions import *  # noqa: F401,F403
