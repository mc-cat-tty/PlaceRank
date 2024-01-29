from typing import Dict, List, Tuple
from placerank.preprocessing import get_default_analyzer
from whoosh.fields import FieldType, Schema, ID, TEXT, KEYWORD
from datetime import datetime
from operator import itemgetter
from collections import defaultdict
import math
import pickle

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


class ReviewsIndex:

    def __init__(self, path = "reviews.pickle"):
        with open("reviews.pickle", "rb") as fp:
            self.index = pickle.load(fp)

    def __todate(self, s: str):
        return datetime.strptime(s, "%Y-%m-%d")

    def get_sentiment_for(self, key, lambda_mult = 1):
        """
        Return the sentiment by exponential decay mean.
        """

        reviews = self.index.get(key)
        
        if not reviews:
            return {}
        
        reference_date = max([datetime.strptime(x, "%Y-%m-%d") for x in map(itemgetter(1), reviews)])

        def decay(date):
            date = self.__todate(date)
            return math.e ** (- lambda_mult * ((reference_date - date).days))
        
        sentiment_vector = defaultdict(int)

        for rid, date, sentiments in reviews:
            for sentiment in sentiments:
                sentiment_vector[sentiment.get("label")] += sentiment.get("score") * decay(date)

        return sentiment_vector

    def get_mean_sentiment_for(self, key, lambda_mult = 1):
        """
        Return the sentiment by simple averaging.
        """

        reviews = self.index.get(key)
        
        if not reviews:
            return {}
        
        reference_date = max([datetime.strptime(x, "%Y-%m-%d") for x in map(itemgetter(1), reviews)])

        def decay(date):
            date = self.__todate(date)
            return math.e ** (- lambda_mult * ((reference_date - date).days))
        
        sentiment_vector = defaultdict(int)

        for rid, date, sentiments in reviews:
            for sentiment in sentiments:
                sentiment_vector[sentiment.get("label")] += sentiment.get("score")

            for k, v in sentiment_vector.items():
                sentiment_vector[k] = v / len(sentiments)

        return sentiment_vector

if __name__ == "__main__":
    ix = ReviewsIndex()
    print(ix.get_sentiment_for('757175885529058316'))
    print(ix.get_mean_sentiment_for('757175885529058316'))