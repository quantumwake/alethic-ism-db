import json
from .semantic_distance import BasicSemanticSearch

embeddings_models = {
    "bert": BasicSemanticSearch(model_name="bert-base-uncased"),
    "st_minilm_l6_v2": BasicSemanticSearch(model_name="sentence-transformers/all-MiniLM-L6-v2"),
    "st_mpnete_v2": BasicSemanticSearch(model_name="sentence-transformers/all-mpnet-base-v2")
}

def create_embedding(text: str, model_name):
    return None

    if model_name not in embeddings_models:
        raise Exception(f'embedding model {model_name} not found in list of models available: {embeddings_models}')

    embedding_model = embeddings_models[model_name]
    if not isinstance(embedding_model, BasicSemanticSearch):
        raise Exception(f'embedding model returned is of type {type(embedding_model)},'
                        f'it must inherit from {type(BasicSemanticSearch)}')

    # create the word embedding to be stored in vector store
    embedding = embedding_model.generate_embedding(text)

    # reshape from 1, D dimensino vector to a D vector and convert to an array of floats, in string format
    return json.dumps(embedding.reshape(-1).numpy().tolist())

    # return embedding.reshape(-1)


def calculate_embeddings(text: str):
    pass
    #return create_embedding(text=text, model_name='st_minilm_l6_v2')


