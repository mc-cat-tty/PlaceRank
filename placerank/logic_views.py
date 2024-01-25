from typing import Dict, List, Tuple
from placerank.preprocessing import get_default_analyzer
from whoosh.fields import FieldType, Schema, ID, TEXT, KEYWORD
from csv import DictReader
import pydash

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

class DocumentLogicView(dict):
    SCHEMA : Dict[str, FieldType] = {
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
        super().__init__({k:record[k] for k in DocumentLogicView.SCHEMA.keys()})
    
    @staticmethod
    def get_schema() -> Schema:
        return Schema(**DocumentLogicView.SCHEMA)

class BenchmarkRecordView:
    """
    A class which both keeps a logic representation (namely, the view) of a benchmark queries record and
    exposes some helper methods to emulate a relational database behavior building on top of different
    CSV files with a common primary key field.
    """
    PK = 'uin_id'
    SCHEMA = {
        'uin_id': int,
        'uin': str,
        'textual_query': str,
        'room_type': str,
        'sentiment_tags': str,
        'ranking': List[int]
    }

    @staticmethod
    def get_view_from_csv(uin_table: List[str], query_table: List[str], ranking_table: List[str]) -> Dict[str, str | int  | List[int]]:
        """
        Takes three tables - uin_table, query_table and ranking_table - as input and joins them on `uin_id` field, returning a view
        of the benchmark query record. The aferomentioned tables must have a well-defined minimal scheme:
            - uin_table (uin_id int pk, uin str)
            - query_table (uin_id int pk, textual_query str, room_type str, sentiment_tags str)
            - ranking_table (uin_id int fk, doc_id int) pk(uin_id, doc_id)
        """
        view = list()
        uin_table = list(DictReader(uin_table))
        query_table = list(DictReader(query_table))
        ranking_table = list(DictReader(ranking_table))
        
        for uin_row in uin_table:
            id = uin_row[BenchmarkRecordView.PK]

            query_rows = (
                pydash.chain(query_table)
                    .filter(lambda r: r[BenchmarkRecordView.PK] == id)
                    .value()
            )
            if len(query_rows) == 0: raise IndexError(f"UIN_ID '{id}' not found in QUERY table")
            assert len(query_rows) == 1

            textual_query = (
                pydash.chain(query_rows)
                    .map(lambda r: r['textual_query'])
                    .map(str)
                    .value()
                    .pop()
            )

            room_type = (
                pydash.chain(query_rows)
                    .map(lambda r: r['room_type'])
                    .map(str)
                    .value()
                    .pop()
            )

            sentiment_tags = (
                pydash.chain(query_rows)
                    .map(lambda r: r['sentiment_tags'])
                    .map(str)
                    .value()
                    .pop()
            )

            ranking_rows = (
                pydash.chain(ranking_table)
                    .filter(lambda r: r[BenchmarkRecordView.PK] == id)
                    .map(lambda r: r['doc_id'])
                    .map(int)
                    .value()
            )
            
            view.append({
                'uin_id': int(id),
                'uin': str(uin_row['uin']),
                'textual_query': textual_query,
                'room_type': room_type,
                'sentiment_tags': sentiment_tags,
                'ranking': ranking_rows
            })

        return view

