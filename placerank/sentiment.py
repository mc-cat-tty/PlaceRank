from transformers import BertTokenizer, AutoModelForSequenceClassification, pipeline
from whoosh.scoring import WeightingModel, BM25F
from placerank.views import ReviewsIndex
import math
import re
import pydash

class GoEmotionsClassifier:

    def __init__(self, model_name='original'):
        self.tokenizer = BertTokenizer.from_pretrained(f"monologg/bert-base-cased-goemotions-{model_name}")
        self.model = AutoModelForSequenceClassification.from_pretrained(f"monologg/bert-base-cased-goemotions-{model_name}", num_labels=28)


    def create_pipeline(self):
        self.goemotions = pipeline(
            model=self.model,
            tokenizer=self.tokenizer,
            task="text-classification",
            top_k=2,
            function_to_apply='sigmoid',
            device="mps"
        )


    def classify_texts(self, texts):
        if not hasattr(self, 'goemotions'):
            self.create_pipeline()
        return self.goemotions(texts)


class BaseSentimentWeightingModel(BM25F):
    def __init__(self, reviews_index_path: str, *args, **kwargs):
        self.use_final = True
        self._user_sentiment = None
        self._reviews_index = ReviewsIndex(reviews_index_path)
        super().__init__(*args, **kwargs)
    
    def _cosine_similarity(self, doc: dict, query: dict):
        """
        Cosine similarity
        """
        
        d_norm = math.sqrt(sum(v**2 for v in doc.values()))
        q_norm = math.sqrt(sum(v**2 for v in query.values()))

        num = sum(doc[k]*query[k] for k in (doc.keys() & query.keys()))
        denom = (d_norm * q_norm)

        return num / denom if denom else 0
    
    def _sentiment_score(self, listing_id, sentiment):
        return self._cosine_similarity(self._get_sentiment_for(listing_id), sentiment)
    
    def _get_sentiment_for(self, listing_id):
        return self._reviews_index.get_sentiment_for(int(listing_id))

    def _combine_scores(self, textual_score, sentiment_score):
        return textual_score * sentiment_score

    def set_user_sentiment(self, user_sentiment):
        user_sentiment = user_sentiment.strip() + ' '
        negated_sentiments = (
            pydash.chain(re.findall(r'\s*not\s+.+?\s+', user_sentiment))
            .map(lambda s: s.strip().split(' ')[1])
            .value()
        )

        self._user_sentiment = {k: 1 if k not in negated_sentiments else -1 for k in user_sentiment.split(" ")}
        if 'not' in self._user_sentiment: del self._user_sentiment['not']


    def final(self, searcher, docnum, textual_score):
        textual_score = super().final(searcher, docnum, textual_score)

        if not self._user_sentiment: return textual_score

        id = searcher.stored_fields(docnum)['id']
        sentiment_score = self._sentiment_score(id, self._user_sentiment)
        return self._combine_scores(textual_score, sentiment_score)


class AdvancedSentimentWeightingModel(BaseSentimentWeightingModel):
    def combine_scores(self, textual_score, sentiment_score, id):
        tmp = textual_score * sentiment_score * self._reviews_index.get_sentiment_len_for(id)
        return tmp

    def final(self, searcher, docnum, textual_score):
        textual_score = super().final(searcher, docnum, textual_score)

        if not self._user_sentiment: return textual_score

        id = searcher.stored_fields(docnum)['id']
        sentiment_score = self._sentiment_score(id, self._user_sentiment)
        return self.combine_scores(textual_score, sentiment_score, id)


if __name__ == "__main__":
    classifier = GoEmotionsClassifier()
    texts = ["it's happened before?! love my hometown of beautiful new ken 😂😂"]
    results = classifier.classify_texts(texts)
    print(results)
