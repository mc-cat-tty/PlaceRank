import os
import csv
from collections import OrderedDict
import torch
from transformers import BertModel, BertTokenizer
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re
nltk.download('stopwords')

# module to generate contextual driven word embeddings with BERT
class BERTEmbeddingsGenerator:

    def __init__(self, model_name='bert-base-uncased'):
        self.model = BertModel.from_pretrained(model_name, output_hidden_states=True)
        self.tokenizer = BertTokenizer.from_pretrained(model_name)
        self.stop_words = set(stopwords.words('english'))

    def bert_text_preparation(self, text):
        text = re.sub(r'[^\w\s]', '', text)
        marked_text = "[CLS] " + text + " [SEP]"
        tokenized_text = self.tokenizer.tokenize(marked_text)
        tokenized_text = [word for word in tokenized_text if word.lower() not in self.stop_words]
        indexed_tokens = self.tokenizer.convert_tokens_to_ids(tokenized_text)
        segments_ids = [1] * len(indexed_tokens)
        tokens_tensor = torch.tensor([indexed_tokens])
        segments_tensor = torch.tensor([segments_ids])
        return tokenized_text, tokens_tensor, segments_tensor

    def get_bert_embeddings(self, tokens_tensor, segments_tensor):
        with torch.no_grad():
            outputs = self.model(tokens_tensor, segments_tensor)
            hidden_states = outputs[2]

        token_embeddings = torch.stack(hidden_states, dim=0)
        token_embeddings = torch.squeeze(token_embeddings, dim=1)
        token_embeddings = token_embeddings.permute(1, 0, 2)

        token_vecs_sum = []
        for token in token_embeddings:
            sum_vec = torch.sum(token[-4:], dim=0)
            token_vecs_sum.append(sum_vec)
        return token_vecs_sum

    # function to export and save the embeddings and their relative metadata
    def _write_embeddings_to_file(self, context_tokens, context_embeddings, output_dir):
        metadata_filepath = os.path.join(output_dir, 'metadata.tsv')
        embeddings_filepath = os.path.join(output_dir, 'embeddings.tsv')

        with open(metadata_filepath, 'w+') as file_metadata:
            for token in context_tokens:
                file_metadata.write(token + '\n')

        with open(embeddings_filepath, 'w+') as tsvfile:
            writer = csv.writer(tsvfile, delimiter='\t')
            for embedding in context_embeddings:
                writer.writerow(embedding.numpy())

    def generate_embeddings(self, sentences, output_dir):
        context_embeddings = []
        context_tokens = []

        for sentence in sentences:
            tokenized_text, tokens_tensor, segments_tensors = self.bert_text_preparation(sentence)
            list_token_embeddings = self.get_bert_embeddings(tokens_tensor, segments_tensors)
            
            tokens = OrderedDict()
            for token in tokenized_text[1:-1]:
                if token in tokens:
                    tokens[token] += 1
                else:
                    tokens[token] = 1
                
                token_indices = [i for i, t in enumerate(tokenized_text) if t == token]
                current_index = token_indices[tokens[token] - 1]
                
                token_vec = list_token_embeddings[current_index]
                context_tokens.append(token)
                context_embeddings.append(token_vec)

        self._write_embeddings_to_file(context_tokens, context_embeddings, output_dir)

# example usage
if __name__ == "__main__":
    texts = [
        "bank", "he eventually sold the shares back to the bank at a premium.", 
        "the bank strongly resisted cutting interest rates."
        # Add more sentences 
    ]

    # choose your output directory in order to save your embeddings
    output_directory = ' '
    
    embeddings_generator = BERTEmbeddingsGenerator()
    embeddings_generator.generate_embeddings(texts, output_directory)
