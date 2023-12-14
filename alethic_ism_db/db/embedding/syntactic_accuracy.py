import nltk
from nltk.translate.meteor_score import meteor_score
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

nltk.download('punkt')
nltk.download('wordnet')

def calculate_bleu(reference, candidate, ):
    reference_tokens = nltk.word_tokenize(reference)
    candidate_tokens = nltk.word_tokenize(candidate)
    return sentence_bleu([reference_tokens],
                         candidate_tokens,
                         smoothing_function=SmoothingFunction().method7)


def calculate_meteor(reference, candidate):
    reference_tokens = nltk.word_tokenize(reference)
    candidate_tokens = nltk.word_tokenize(candidate)
    return meteor_score([reference_tokens], candidate_tokens)


def calculate_ter(reference, candidate):
    reference_tokens = nltk.word_tokenize(reference)
    candidate_tokens = nltk.word_tokenize(candidate)
    # return pyter.ter(candidate_tokens, reference_tokens)
    raise NotImplementedError()

