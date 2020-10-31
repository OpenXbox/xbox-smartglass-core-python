from fastapi import APIRouter
from .. import schemas, SMARTGLASS_PACKAGENAMES

router = APIRouter()


@router.get('/', response_model=schemas.IndexResponse)
def get_index():
    import pkg_resources

    versions = {}
    for name in SMARTGLASS_PACKAGENAMES:
        try:
            versions[name] = pkg_resources.get_distribution(name).version
        except Exception:
            versions[name] = None

    return schemas.IndexResponse(
        versions=versions,
        doc_path='/docs'
    )
