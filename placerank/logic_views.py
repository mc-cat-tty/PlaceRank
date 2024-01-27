from typing import Dict
from dataclasses import Field
from placerank.preprocessing import getDefaultAnalyzer
from whoosh.fields import FieldType, Schema, ID, TEXT, KEYWORD

class InsideAirbnbSchema(Schema):
    """
    A whoosh.fields.Schema class for inverted index schema tailored to InsideAirbnb dataset
    that supports custom analyzers.
    """

    def __init__(self, analyzer = None):
        if not analyzer:
            analyzer = getDefaultAnalyzer()

        self.logicview: Dict[str, FieldType] = {
            "id": ID(stored = True, unique=True),
            "name": TEXT(stored = True, field_boost=1.5),
            "room_type": KEYWORD(stored=True, lowercase=True),
            "description": TEXT(analyzer=getDefaultAnalyzer()),
            "neighborhood_overview": TEXT(analyzer=getDefaultAnalyzer())
        }
        
        super().__init__(**self.logicview)

    def get_document_logic_view(self, record: dict) -> dict:
        """
        Extracts only the required keys from a dictionary representing a dataset record.
        The required keys are specified in `self.logicview`.
        """
        return {k:record[k] for k in self.logicview.keys()}
