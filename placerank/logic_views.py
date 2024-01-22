from whoosh.fields import Schema, ID, TEXT

class DocumentLogicView(dict):
    VIEW = {
        "id": ID(stored = True, unique=True),
        "name": TEXT(stored = True),
        "room_type": TEXT(stored=True),
        "description": TEXT,
        "neighborhood_overview": TEXT
    }
    
    def __init__(self, record: dict):
        """
        Extracts only the required keys from a dictionary representing a dataset record.
        The required keys are specified in the `keys` list below.
        """
        super().__init__({k:record[k] for k in DocumentLogicView.VIEW})
    
    @staticmethod
    def get_schema() -> Schema:
        return Schema(**DocumentLogicView.VIEW)
