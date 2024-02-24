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
from alethic_ism_db.db.embedding.semantic_distance import BasicSemanticSearch
from alethic_ism_db.db.embedding.syntactic_accuracy import calculate_bleu, calculate_meteor

reference_sentence = 'Cows are thoughtful, intelligent beings with family structures.'
other_sentences = ['Cows are sentient intelligent beings',
                   'Cows are a food source for humans',
                   'Cows are farm animals used by humans for their milk and meat',
                   'Cows are protesting against having been domesticated farm animals.',
                   'Cows love being domesticated animals used for their meat',
                   'Cows do not want to be a food source for humans',

                   # same as reference for baseline
                   'Cows are domesticated farm animals, they are only used for their meat, milk and skin',
                   'Kühe sind domestizierte Nutztiere, die hauptsächlich wegen ihres Fleisches, ihres Leders und ihrer Milch genutzt werden.',
                   'Les vaches sont des animaux domestiques utilisés principalement pour leur viande, leur cuir et leur lait.']

semantics = [
    BasicSemanticSearch(model_name="bert-base-uncased"),
    BasicSemanticSearch(model_name="sentence-transformers/all-MiniLM-L6-v2"),
    BasicSemanticSearch(model_name="sentence-transformers/all-mpnet-base-v2")
]

for semantic in semantics:
    print(f''.join(['-' for _ in range(1, 80)]))
    print(f'Using the {semantic} with model {semantic.model_name} to calculate sentence similarity distance calculations')
    distances_from_reference = semantic.calculate_distances(reference_sentence=reference_sentence,
                                                            other_sentences=other_sentences)

    print(f"Calculated semantic distances from reference sentence: {reference_sentence}")
    for idx, distance in enumerate(distances_from_reference):
        print(f' - {distance}\t\t{other_sentences[idx]}')


print(f''.join(['-' for _ in range(1, 80)]))
print(f"Calculated BLEU, METEOR and TER scores from reference sentence: {reference_sentence}")
for idx, sentence in enumerate(other_sentences):
    bleu_score = calculate_bleu(reference_sentence, sentence)
    meteor_score = calculate_meteor(reference_sentence, sentence)
    # ter_score = calculate_ter(reference_sentence, sentence)

    formatted_bleu = "{:.2e}".format(bleu_score)  # Scientific notation with 2 decimal places
    formatted_meteor = "{:.4f}".format(meteor_score)  # Standard decimal with 4 decimal places
    # formatted_ter = "{:.4f}".format(ter_score)  # Standard decimal with 4 decimal places
    formatted_ter = "N/A"
    print(f' - blue: {formatted_bleu}\t meteor: {formatted_meteor}\t ter: {formatted_ter}\t\t{other_sentences[idx]}')
