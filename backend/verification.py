import re
import torch
from nltk.tokenize import sent_tokenize
from constants import *

def split_text_by_pubmed_references(text:str) -> list:
    """
    param:
    text: it is the response of our LLM

    return:
    it returns a list where each element is composed by [Pmid, claim]
    if there are no reference it returns an empy list 
    """

    previous_sentences = ""
   
    results = []

    # parameter used to see if there are references, we assume at the beggining no reference
    no_reference = True 
   
    regular_expression = r'<a href=".*?" target="_blank">(.*?)<\/a>'

    # used to verify if the first sentence has the reference, it is usually the general response
    regular_expression_removing = r'<a href=".*?" target="_blank">'
    
    pattern = re.compile(regular_expression)

    sentences = sent_tokenize(text)
    

    # Search for the pattern in the text
    matches = list(pattern.finditer(text))
   

    start_pos = 0
    for match in matches:
        no_reference = False # reference found 
        pubmed_number = match.group(0) if match.group(0) != None else match.group(1) if match.group(1) != None else match.group(2)
        
        # exctracting just the number (pubmid)
        pubmed_number = re.sub(r'<.*?>', '', pubmed_number)
        pubmed_number = re.sub(r'\D', '', pubmed_number)
       
        end_pos = match.start()  
        text_segment = text[start_pos:end_pos].strip()  
        
        # text cleaning
        text_segment = text_segment.replace("</a>", "")
        text_segment = re.sub(r'[\s\[\(\)\],;.]*$', '', previous_sentences + text_segment)
        
        if pubmed_number and text_segment:
            
            text_segment = re.sub(r'^[\s\[\(\)\],;.]*', '', text_segment)
        
            text_segment = re.sub(r'^[\)\]]?[.,;]', '', text_segment)

            results.append([pubmed_number,text_segment])

            start_pos = match.end()
        elif pubmed_number and len(results) > 0 and not text_segment:
            
            results.append([pubmed_number,results[-1][1]])

            start_pos = match.end()

        
        previous_sentences = ""


    if re.search(regular_expression_removing, sentences[0]) == None:
        
        results[0][1] = results[0][1].replace(sentences[0], "")
        results.insert(0, [NO_REFERENCE_NUMBER,sentences[0]])


    if text[start_pos:] != "":
        results.append([NO_REFERENCE_NUMBER,text[start_pos:]])
        
    return results if no_reference == False else []


def verification_claim(claims: list, abstracts: dict, verification_model, verification_tokenizer):
    if not claims:
        yield {"claim": "The whole abstract", "result": NO_REFERENCE}
    
    for element in claims:
        pmid, claim = element
        if pmid in abstracts:
            
            model_instruction = verification_tokenizer.cls_token + claim + verification_tokenizer.sep_token + abstracts[pmid]["text"] + verification_tokenizer.sep_token
            inputs = verification_tokenizer(model_instruction, return_tensors="pt")
            with torch.no_grad(): 
                outputs = verification_model(**inputs)
                logits = outputs.logits
                prediction = torch.argmax(logits).numpy()
                label_prediction = LABELS[prediction] 
                yield {"claim": claim, "pmid": pmid, "result": label_prediction}
        else:
            yield {"claim": claim, "result": NO_REFERENCE}


