from typing import Dict, NamedTuple
from placerank.preprocessing import get_default_analyzer
from whoosh.fields import FieldType, Schema, ID, TEXT, KEYWORD
from enum import Flag, auto, verify, NAMED_FLAGS


class DocumentLogicView(dict):
    SCHEMA: Dict[str, FieldType] = {
        "id": ID(stored = True, unique=True),
        "name": TEXT(stored = True, field_boost=1.5),
        "room_type": KEYWORD(stored=True, lowercase=True),
        "description": TEXT(analyzer=get_default_analyzer()),
        "neighborhood_overview": TEXT(analyzer=get_default_analyzer())
    }
    
    def __init__(self, record: dict):
        """
        Extracts only the required keys from a dictionary representing a dataset record.
        The required keys are specified in the `SCHEMA` class field.
        """
        super().__init__({k: record[k] for k in DocumentLogicView.SCHEMA.keys()})
    
    @staticmethod
    def get_schema() -> Schema:
        return Schema(**DocumentLogicView.SCHEMA)


@verify(NAMED_FLAGS)
class SearchFields(Flag):
    NAME = auto()
    ROOM_TYPE = auto()
    DESCRIPTION = auto()
    NEIGHBORHOOD_OVERVIEW = auto()


class QueryView(NamedTuple):
    textual_query: str
    search_fields: SearchFields = 0
    room_type: str = ''
    sentiment_tags: str = ''

class ResultView(NamedTuple):
    id: int
    name: str
    room_type: str