from flask import Blueprint
routes = Blueprint('routes', __name__)

from .index import *
from .auth import *
from .device import *
from .web import *
from .versions import *
