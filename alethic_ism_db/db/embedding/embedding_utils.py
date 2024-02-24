# The Alethic Instruction-Based State Machine (ISM) is a versatile framework designed to 
# efficiently process a broad spectrum of instructions. Initially conceived to prioritize
# animal welfare, it employs language-based instructions in a graph of interconnected
# processing and state transitions, to rigorously evaluate and benchmark AI models
# apropos of their implications for animal well-being. 
# 
# This foundation in ethical evaluation sets the stage for the framework's broader applications,
# including legal, medical, multi-dialogue conversational systems.
# 
# Copyright (C) 2023 Kasra Rasaee, Sankalpa Ghose, Yip Fai Tse (Alethic Research) 
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# 
# 
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


