import nltk, torch, pydash
from typing import List
from operator import itemgetter
from huggingface_hub import snapshot_download
from nltk.corpus import wordnet as wn
from transformers import BertTokenizer, BertModel, BertForMaskedLM, FillMaskPipeline
from abc import ABC, abstractmethod


def setup(repo_ids: List[str], cache_dir: str):
    for id in repo_ids:
        snapshot_download(repo_id = id, cache_dir = cache_dir)
    nltk.download("wordnet")


class QueryExpansionService(ABC):
    """
    A class that implements a query expansion service.
    Exposes the `expand` method.
    """

    @abstractmethod
    def expand(query: str) -> str:
        ...


class NoQueryExpansion(QueryExpansionService):
    """
    A mock object that does nothing on the query
    """
    def expand(self, query: str) -> str:
        return query


class ThesaurusQueryExpansion(QueryExpansionService):
    """
    A WordNet-based - aka thesaurus-based - query expansion service.
    """
    def __init__(self, hf_cache: str):
        self.tokenizer = BertTokenizer.from_pretrained('bert-base-uncased', cache_dir = hf_cache)
        self.encoder = BertModel.from_pretrained('bert-base-uncased', output_hidden_states = True, cache_dir = hf_cache)
        self.cos_sim = torch.nn.CosineSimilarity(dim  = 0)

    def _tokenize(self, query: str):
        return self.tokenizer.tokenize(query)
    
    def _similarity(self, x, y):
        return self.cos_sim(x, y)

    def _get_embedding(self, query: str):
        tokens = self._tokenize(query)
        input_ids = self.tokenizer.convert_tokens_to_ids(tokens)

        input_ids = torch.tensor(input_ids).unsqueeze(0)
        with torch.no_grad():
            outputs = self.encoder(input_ids)
            embedding = outputs.last_hidden_state[0]

        return embedding.mean(dim = 0)
    
    def _formattable_token(self, original: List[str], idx: int) -> str:
        tmp = original[:]
        tmp[idx] = '{}'
        fmt = ' '.join(tmp)
        return fmt 

    def expand(self, query: str, max_results: int = 5, confidence_threshold: float = 0) -> str:
        tokens = self._tokenize(query)
        query_embedding = self._get_embedding(query)
        expanded_query = ""
       
        for idx, token in enumerate(tokens):
            query_fmt = self._formattable_token(tokens, idx) 

            candidates = (
                pydash.chain([s.lemma_names() for s in wn.synsets(token)])
                    .flatten_deep()
                    .sorted_uniq()
                    .map(lambda c: c.replace('_', ' '))
                    .value()
            )

            similarities = (
                pydash.chain(candidates)
                    .map(lambda c: query_fmt.format(c))
                    .map(self._get_embedding)
                    .map(lambda x: self._similarity(x, query_embedding))
                    .value()
            )

            expansions = (
                pydash.chain(candidates)
                    .zip(similarities)
                    .filter(lambda t: t[1] > confidence_threshold)
                    .sort(key = itemgetter(1), reverse = True)
                    .map(itemgetter(0))
                    .take(max_results)
                    .value()
            )
            
            expanded_query += " " + ' '.join(expansions)

        return expanded_query

class LLMQueryExpansion(QueryExpansionService):
    """
    A BERT-based - aka LLM-based - query expansion service.
    """
    def __init__(self, hf_cache: str):
        self.tokenizer = BertTokenizer.from_pretrained('bert-base-uncased', cache_dir = hf_cache)
        self.encoder_model = BertModel.from_pretrained('bert-base-uncased', output_hidden_states = True, cache_dir = hf_cache)
        
        from transformers import logging
        logging.set_verbosity_error()
        unmasker_model = BertForMaskedLM.from_pretrained('bert-large-uncased-whole-word-masking', cache_dir = hf_cache, )
        logging.set_verbosity_warning()
        
        self.unmasker = FillMaskPipeline(model = unmasker_model, tokenizer = self.tokenizer, tokenizer_kwargs = {"truncation": True})
        self.cos_sim = torch.nn.CosineSimilarity(dim  = 0)
    
    def _tokenize(self, query: str):
        return self.tokenizer.tokenize(query)

    def _similarity(self, x, y):
        return self.cos_sim(x, y)

    def _get_embedding(self, query: str):
        tokens = self._tokenize(query)
        input_ids = self.tokenizer.convert_tokens_to_ids(tokens)

        input_ids = torch.tensor(input_ids).unsqueeze(0)
        with torch.no_grad():
            outputs = self.encoder_model(input_ids)
            embedding = outputs.last_hidden_state[0]

        return embedding.mean(dim = 0)
    
    def _formattable_token(self, original: List[str], idx: int) -> str:
        tmp = original[:]
        tmp[idx] = '{}'
        fmt = ' '.join(tmp)
        return fmt
    
    def _mask_token(self, original: List[str], idx: int) -> str:
        tmp = original[:]
        tmp[idx] = '[MASK]'
        masked = ' '.join(tmp)
        return masked

    def expand(self, query: str, max_results: int = 3, confidence_threshold: float = 0.9, overprediction: int = 5) -> str:
        tokens = self._tokenize(query)
        query_embedding = self._get_embedding(query)
        expanded_query = ""
       
        for idx, token in enumerate(tokens):
            candidates = self.unmasker(self._mask_token(['[CLS] '] + tokens + [' [SEP]'], idx+1), top_k = max_results*overprediction)

            similarities = (
                pydash.chain(candidates)
                    .map(itemgetter('sequence'))  # Get complete sentence
                    .map(self._get_embedding)
                    .map(lambda x: self._similarity(x, query_embedding))
                    .value()
            )

            expansions = (
                pydash.chain(candidates)
                    .map(itemgetter('token_str'))
                    .zip(similarities)
                    .filter(lambda t: t[1] > confidence_threshold)
                    .sort(key = itemgetter(1), reverse = True)
                    .map(itemgetter(0))
                    .take(max_results)
                    .value()
            )
            
            expanded_query += " " + ' '.join(set(expansions + [token]))

        return expanded_query


def main():
    qe_wn = ThesaurusQueryExpansion('hf_cache')
    qe_bert = LLMQueryExpansion('hf_cache')

    query = 'modern shared room near Harvard.'
    print(f'{query=}')
    print(qe_wn.expand('modern shared room near Harvard.', 3, 0.9))
    print(qe_bert.expand('modern shared room near Harvard.', 3, 0.9, 5))

if __name__ == '__main__':
    main()