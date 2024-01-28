from __future__ import annotations
from typing import Dict, NamedTuple
from placerank.preprocessing import get_default_analyzer
from whoosh.fields import FieldType, Schema, ID, TEXT, KEYWORD
from enum import Flag, auto, verify, NAMED_FLAGS

class InsideAirbnbSchema(Schema):
    """
    A whoosh.fields.Schema class for inverted index schema tailored to InsideAirbnb dataset
    that supports custom analyzers.
    """

    def __init__(self, analyzer = None):
        if not analyzer:
            analyzer = get_default_analyzer()

        self.logicview: Dict[str, FieldType] = {
            "id": ID(stored = True, unique=True),
            "name": TEXT(stored = True, field_boost=1.5),
            "room_type": KEYWORD(stored=True, lowercase=True),
            "description": TEXT(analyzer=get_default_analyzer()),
            "neighborhood_overview": TEXT(analyzer=get_default_analyzer())
        }
        
        super().__init__(**self.logicview)

    def get_document_logic_view(self, record: dict) -> dict:
        """
        Extracts only the required keys from a dictionary representing a dataset record.
        The required keys are specified in `self.logicview`.
        """
        return {k:record[k] for k in self.logicview.keys()}

class DocumentView(NamedTuple):
    """
    Adapter class to a document that instances an immutable tuple
    """
    id: str
    name: str
    room_type: str
    description: str
    neighborhood_overview: str

    @staticmethod
    def from_record(record: dict) -> DocumentView:
      return {k: record[k] for k in DocumentView._fields}


@verify(NAMED_FLAGS)
class SearchFields(Flag):
    """
    Enumeration of searchable fields
    """
    NAME = auto()
    ROOM_TYPE = auto()
    DESCRIPTION = auto()
    NEIGHBORHOOD_OVERVIEW = auto()


class QueryView(NamedTuple):
    """
    Adapter class to a query that instances an immutable tuple
    """
    textual_query: str
    search_fields: SearchFields = 0
    room_type: str = ''
    sentiment_tags: str = ''

class ResultView(NamedTuple):
    """
    Adapter class to a result (hit) that instances an immutable tuple
    """
    id: str
    name: str
    room_type: str