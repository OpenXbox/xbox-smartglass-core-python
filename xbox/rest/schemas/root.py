from typing import Dict, Optional
from pydantic import BaseModel

class IndexResponse(BaseModel):
    versions: Dict[str, Optional[str]]
    doc_path: str
