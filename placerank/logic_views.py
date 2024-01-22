from typing import Dict
from dataclasses import Field
from placerank.preprocessing import getDefaultAnalyzer
from whoosh.fields import FieldType, Schema, ID, TEXT, KEYWORD

class DocumentLogicView(dict):
    SCHEMA : Dict[str, FieldType] = {
        "id": ID(stored = True, unique=True),
        "name": TEXT(stored = True, field_boost=1.5),
        "room_type": KEYWORD(stored=True, lowercase=True),
        "description": TEXT(analyzer=getDefaultAnalyzer()),
        "neighborhood_overview": TEXT(analyzer=getDefaultAnalyzer())
    }
    
    def __init__(self, record: dict):
        """
        Extracts only the required keys from a dictionary representing a dataset record.
        The required keys are specified in the `keys` list below.
        """
        super().__init__({k:record[k] for k in DocumentLogicView.SCHEMA.keys()})
    
    @staticmethod
    def get_schema() -> Schema:
        return Schema(**DocumentLogicView.SCHEMA)
