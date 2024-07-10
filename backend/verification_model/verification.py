import re
import torch
from nltk.tokenize import sent_tokenize
import time
import numpy as np
from constants import *
import numpy as np
import re
import nltk
from nltk.tokenize import sent_tokenize
from utils import calculate_similarity, clean_text, extract_pubmed_references

nltk.download('punkt')



def find_max_similarity_and_count(splits: list, sentence: str, documents: dict, start: int, step: int, sentence_model) -> (float, int):
    """
    Find the maximum similarity and count of the abstract to analyze cited in the same sentence..

    param:
    splits: The list of splits containing [Pmid, sentence] pairs.
    sentence:The sentence to compare for similarity.
    documents: The dictionary containing the abstract in the form [pmid, dict["text": text of the abstract]].
    start:  The starting index for the search.
    step: The step direction for the search (positive for forward, negative for backward).
    sentence_model: The model used to encode the sentences.

    return:
    tuple - The maximum similarity score and the count of the abstract to analyze cited in the same sentence.
    """
    max_similarity = 0
    count = 0
    j = start
    
    # this variable is needed to check if we are analyzing the same previous/next sentence but with a different pmid associated
    sentence_to_check = "" 
    while 0 <= j < len(splits):
        
        pmid_to_check = splits[j][0]
        current_sentence = splits[j][1]

        sentence_to_check = current_sentence if j == start else sentence_to_check
        # the loop has been created for the case of when a sentence is cited by more pmid
        # so the loop stops continues because it analyze the same sentence but associated with an other pmid
        if current_sentence != sentence_to_check:
            break

        # Calculate similarity score
        similarity_score = calculate_similarity(sentence, documents[pmid_to_check]['text'], sentence_model)
        max_similarity = max(max_similarity, similarity_score)
        count += 1
        j += step

    return max_similarity, count

def correct_splits(splits: list, documents: dict, sentence_model) -> list:
    """
    Correct the splits by merging the sentences with no references, the merge is based computing the highest similarity between the previous and the next sentence,
    taking in account the all possible pubmed references of a sentence.

    param:
    splits: The list of splits containing [Pmid, sentence] pairs.
    documents: The dictionary containing the abstract in the form [pmid, dict["text": text of the abstract]].
    sentence_model: The model used to encode the sentences.

    return:
    list - The corrected list of splits.
    """
    for i, (pmid, sentence) in enumerate(splits):
        
        # the assumptionis that the first sentence: "Premise" and last sentence "Conclusion" could not be associated to any Pubmed reference
        if i == 0 or i == len(splits) - 1 or pmid != NO_REFERENCE_NUMBER:
            continue

        # Find maximum similarity and count in both directions
        prev_max_sim, prev_count = find_max_similarity_and_count(splits, sentence, documents, i - 1, -1, sentence_model)
        next_max_sim, next_count = find_max_similarity_and_count(splits, sentence, documents, i + 1, 1, sentence_model)

        if next_max_sim >= prev_max_sim:
            merge_count, step = next_count, 1
        else:
            merge_count, step = prev_count, -1

        for j in range(1, merge_count + 1):
            target_index = i + j * step
            if 0 <= target_index < len(splits):
                if step == 1:
                    splits[target_index][1] = sentence + ' ' + splits[target_index][1]
                else:
                    splits[target_index][1] += ' ' + sentence

    # Remove the split with No Reference because has been merged with the previous or next sentence based on the highest similarity with the model
    # first sentence: "Premise" and last sentence "Conclusion" could not be associated to any Pubmed reference, so are not deleted
    splits = [split for split in splits if split[0] != -1 or split == splits[0] or split == splits[-1]]
    return splits




def split_text_by_pubmed_references(text: str, documents: dict, sentence_model) -> list:
    """
    Split the text by PubMed references and return a list of [Pmid, sentence].
    If there are no references, return an empty list.

    param:
    text: The input text to split by PubMed references.
    documents: The dictionary containing the abstract in the form [pmid, dict["text": text of the abstract]].
    sentence_model: The model used to encode the sentences.

    return:
    The list of [Pmid, sentence] pairs.
    """
    text = clean_text(text)
    sentences = sent_tokenize(text)
    matches = extract_pubmed_references(text)

    if not matches:
        return []

    results = []

    for sentence in sentences:
        matches = extract_pubmed_references(sentence)

        if not matches:
            if results and results[-1][0] == NO_REFERENCE_NUMBER:
                results[-1][1] += sentence
            else:
                results.append([-1, sentence])
        else:
            for match in matches:
                pubmed_number = re.sub(r'\D', '', match.group(0))
                
                # if len the result is less then a small value it means that there are edge case that leads to a wrong split so we merge with the last one
                # the wrong splits are generate by the tokenizer of nltk for edge cases
                if results and len(results[-1][1]) < 4 and results[-1][0] == NO_REFERENCE_NUMBER:
                    results[-1] = [pubmed_number, results[-1][1] + sentence]
                else:
                    results.append([pubmed_number, sentence])

    return correct_splits(results, documents, sentence_model)


def verification_format(claims:list) -> [ [str, list] ]:
    """
    param:
    claims: list of claim for each pmid

    return:
    it returns a list where each element is composed by [claim, [pmid1,pmid2]] 
    in order to manage better the situation with the front end part
    """

    if claims == []:
        return []
    
    pmid, claim = claims[0]

    output_format = [[claim, [pmid]]]
    for pmid, claim in claims[1:]:
        if claim == output_format[-1][0]: # check if the claim is present
            output_format[-1][1].append(pmid)
        else:
            output_format.append([claim, [pmid]])
    
    return output_format

            
def converting_document_for_verification(documents:list) -> dict:
    """
    This is a function to convert the data type of the document in order to reducing the 
    complexity during the search from O(N^2) to O(N)

    param:
    documents: list of documents found from IR component

    return:
    documents_found: return a dict of document found in this way:
        key is the pmid
        item is a dict contain the "text" and as value the text of the document
    """
    if len(documents) == 0:
        return {}

    documents_found = {}
    for document in documents:   
        documents_found[document["pmid"]] = {"text": document["text"]}
    
    return documents_found


def find_closest_sentence(claim: str, abstract: str, sentence_model) -> str:
    """
    It founds the similar sentence in the abstarct:
    param:
        claim: is the sentence to use
        abstract: is the abstract where to find the closest sentence
    return:
        the closest sentence in the abstract
    """
    abstract_sentence = sent_tokenize(abstract)
    claim_vector = sentence_model.encode(claim)
    max_dot_product = float('-inf')
    closest_sentence = None
    for sentence in abstract_sentence:
        sentence_vector = sentence_model.encode(sentence)
        dot_product = np.dot(claim_vector,sentence_vector)
        if dot_product > max_dot_product:
            max_dot_product = dot_product
            closest_sentence = sentence
    return closest_sentence




def verification_claim(claims: list, abstracts: dict, verification_model, verification_tokenizer, sentence_model):
    if claims == []:
        yield  {}
    
    for element in claims:
        
        claim, pmids = element
        results = {"claim":claim, "result":{}}
        
        for pmid in pmids:
            if pmid in abstracts:
                results['result'][pmid] = {}

                # Adding the title as information to sent, the title is divided for each document by \n\n
                title = abstracts[pmid]["text"].split("\n\n")[0] 
                abstract = ' '.join(abstracts[pmid]["text"].split("\n\n")[1:])
                results['result'][pmid]['title'] = title
                
                # Inference
                model_instruction = verification_tokenizer.cls_token + claim + verification_tokenizer.sep_token + abstracts[pmid]["text"] + verification_tokenizer.sep_token
                inputs = verification_tokenizer(model_instruction, return_tensors="pt")
                with torch.no_grad(): 
                    outputs = verification_model(**inputs)
                    logits = outputs.logits
                    prediction = torch.argmax(logits).numpy()
                    label_prediction = LABELS[prediction] 
                    results["result"][pmid]["label"] = label_prediction
                    if label_prediction == SUPPORT or label_prediction == CONTRADICT:
                        closest_sentence = find_closest_sentence(claim, abstract, sentence_model)
                        results["result"][pmid]["closest_sentence"] = closest_sentence
            else:
                results["result"][NO_REFERENCE_NUMBER] = {}
                results["result"][NO_REFERENCE_NUMBER]['label'] = NO_REFERENCE
                
        yield results
        


