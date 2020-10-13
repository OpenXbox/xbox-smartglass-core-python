from fastapi import APIRouter
from ..schemas import root
from .. import SMARTGLASS_PACKAGENAMES

router = APIRouter()

@router.get('/', response_model=root.IndexResponse)
def get_index():
    import pkg_resources

    versions = {}
    for name in SMARTGLASS_PACKAGENAMES:
        try:
            versions[name] = pkg_resources.get_distribution(name).version
        except Exception:
            versions[name] = None

    return root.IndexResponse(
        versions=versions,
        doc_path='/docs'
    )
