from typing import Dict, Optional
from pydantic import BaseModel

class GeneralResponse(BaseModel):
    success: bool
    details: Optional[Dict[str, str]]
