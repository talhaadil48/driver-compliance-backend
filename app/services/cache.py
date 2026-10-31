import time
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.document_type import DocumentType

_DOC_TYPES_CACHE: Optional[List[DocumentType]] = None
_DOC_TYPES_CACHE_TIME: float = 0
CACHE_TTL = 60.0

def get_cached_doc_types(db: Session) -> List[DocumentType]:
    global _DOC_TYPES_CACHE, _DOC_TYPES_CACHE_TIME
    now = time.time()
    if _DOC_TYPES_CACHE is not None and (now - _DOC_TYPES_CACHE_TIME) < CACHE_TTL:
        return _DOC_TYPES_CACHE

    doc_types = db.query(DocumentType).order_by(DocumentType.is_custom.asc(), DocumentType.id.asc()).all()
    _DOC_TYPES_CACHE = doc_types
    _DOC_TYPES_CACHE_TIME = now
    return doc_types

def invalidate_doc_types_cache():
    global _DOC_TYPES_CACHE
    _DOC_TYPES_CACHE = None
