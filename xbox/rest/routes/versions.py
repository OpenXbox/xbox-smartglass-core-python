from flask import current_app as app
from . import routes


@routes.route('/versions')
def library_versions():
    import pkg_resources

    versions = {}
    for name in app.smartglass_packetnames:
        try:
            versions[name] = pkg_resources.get_distribution(name).version
        except Exception:
            versions[name] = None

    return app.success(versions=versions)
