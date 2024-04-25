
# from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F


class SemanticSearchBase:
    def __init__(self):
        raise NotImplementedError("This is a base class and should not be instantiated directly.")

## TODO biases on the statements on various models

    def mean_pooling(self, model_output, attention_mask):
        # Extract the first element of model_output which contains token embeddings
        token_embeddings = model_output[0]

        # Expand the attention mask to match the dimensions of token_embeddings.
        # This addition of an extra dimension allows for element-wise multiplication.
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()

        # Perform element-wise multiplication of token_embeddings with the expanded attention mask.
        # This operation zeroes out embeddings for padding tokens, focusing only on actual content tokens.
        focused_embeddings = token_embeddings * input_mask_expanded

        # Calculate the sum of non-padding tokens in each sentence for use in averaging.
        # This step counts how many actual content tokens (non-padded) are present in each sentence.
        focused_embeddings_count = input_mask_expanded.sum(1)

        # Compute the mean of embeddings.
        # This is achieved by summing the focused embeddings (where padding is zeroed out) and then
        # dividing by the number of actual content tokens to get the average embedding per sentence.
        # The use of torch.clamp ensures no division by zero in cases where a sentence might be fully padded.
        return torch.sum(focused_embeddings, 1) / torch.clamp(focused_embeddings_count, min=1e-9)

    def generate_embedding(self, sentences: [str]):
        # Tokenize the sentence. This process involves converting words to token IDs,
        # adding necessary special tokens, and creating an attention mask. The tokenizer
        # prepares the input in the format expected by the model.
        encoded_input = self.tokenizer(sentences, return_tensors='pt', padding=True, truncation=True)

        # Disable gradient calculations. This is important for inference to reduce memory usage
        # and improve computational efficiency since gradients are not needed.
        with torch.no_grad():
            # Feed the tokenized input to the model. The model returns several outputs including
            # the token embeddings. The token embeddings are vectors representing each token in the sentence.
            # The shape of the output is typically (batch_size, num_tokens, embedding_dim), where
            # embedding_dim is the size of each token embedding vector (e.g., 384).
            model_output = self.model(**encoded_input)

        # Apply mean pooling to the model's output and the attention mask. Mean pooling aggregates
        # the token embeddings into a single sentence-level embedding, taking into account the
        # attention mask to exclude padding tokens from the aggregation.
        return self.mean_pooling(model_output, encoded_input['attention_mask'])

    def generate_normalized_embeddings(self, sentences: [str]):
        embeddings = self.generate_embedding(sentences)

        # Normalize embeddings such that we can calcul
        embeddings = F.normalize(embeddings, p=2, dim=1)

        # return normalized embeddings
        return embeddings

    def calculate_distances(self, reference_sentence: str, other_sentences: [str]):
        # Generate embeddings for the reference sentence and other sentences
        all_sentences = [reference_sentence] + other_sentences
        all_embeddings = self.generate_normalized_embeddings(all_sentences)

        # Extract the embedding for the reference sentence
        ref_embedding = all_embeddings[0]

        # Initialize a list to store distances
        distances = []

        # Calculate distance from the reference sentence to each of the other sentences
        for emb in all_embeddings[1:]:
            # Using cosine similarity as the distance metric. This ranges from -1 (opposite) to 1 (identical).
            # A higher score indicates greater similarity.
            # For other distance metrics like Euclidean, you can use torch.norm or other appropriate functions.
            distance = torch.nn.functional.cosine_similarity(ref_embedding, emb, dim=0)
            distances.append(distance.item())

        return distances


class BasicSemanticSearch(SemanticSearchBase):
    def __init__(self, model_name):
        self.model_name = model_name
        # self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        # self.model = AutoModel.from_pretrained(model_name)

