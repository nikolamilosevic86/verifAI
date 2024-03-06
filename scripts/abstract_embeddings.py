from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer
import pandas as pd
import os
import time
import json
import torch
import nltk
nltk.download('punkt')
from nltk.tokenize import sent_tokenize
import logging
# Suppress the specific warning
logging.getLogger("transformers.tokenization_utils_base").setLevel(logging.ERROR)


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device {device}")

# Max split
MAX_SPLIT = 512

# path variables
path = "../outputNJSONextracted"  # Directory containing your JSON files
path_to_save = "../NJSON_embeddings"
model_card = 'sentence-transformers/msmarco-distilbert-base-tas-b'
json_wrong_documents = 'wrong_documents.json'

# model variable
tokenizer = AutoTokenizer.from_pretrained(model_card)
model = SentenceTransformer(model_card)
model.to(device)

# list of wrong documents
wrong_documents = []

# creating path to save file
if not os.path.exists(path_to_save):
    # If the folder doesn't exist, create it
    os.makedirs(path_to_save)
    print(f"The folder '{path_to_save}' has been created.")



def check_results(splitted_documents: list, max_split:int = MAX_SPLIT) -> bool:
    """
    The functionn check for each split if there is a parsed split with a number of token greater than max split
    
    It return: False when there is/are mistake/s
               True if everything is correct
    """
    for document in splitted_documents:
        if len(tokenizer.encode(document, add_special_tokens=True)) > max_split:
            # wrong documents find
            return False
    return True

def remove_outer_square_brackets(title:str) -> str:
    """
    It takes as input a special title with start with [ and end with ]
    The function removes only the first and the last one square bracket in the title

    Many title ara in this format: [Enzyme diagnosis of acute and chronic hepatitis].
    We want as output:              Enzyme diagnosis of acute and chronic hepatitis.
    """
    start_index = title.find('[') # find the index of first square bracket
    end_index = title.rfind(']') # find the index of theh last square bracket 
    if start_index != -1 and end_index != -1:
        return title[start_index + 1: end_index] + title[end_index+1:]
    else:
        return title 

def title_conversion(title:str) -> str:
    """
    The function takes in input the title string, 
    Return the string without useless space and adds at the end the correct marks or full stop
    """

    # Delete useless white space and substituiting the \n with Whitespace from the title
    title = title.replace('\n',' ').strip() 
    if title[0] == '[':
      title = remove_outer_square_brackets(title)

    if title[-1] == '.' or title[-1] == '?' or title[-1] == '!':
        return title
    # if no marks, we insert the full stop
    return title + '.' 
    

def split_text(text: str, max_split: int = MAX_SPLIT) -> list:
    """
    The function takes in input an abstract and return a list of part of abstract divide in base to the model.
    
    The code is structured in this way:

    1) Starting from the title: Begin processing by considering the title.
    2) Adding each abstract sentence: Incorporate each sentence from the abstract.
    3) Segmenting when reaching a limit: If the constructed text reaches a limit, 
              insert the accumulated text up to the previous sentence into a list, and continue processing from the current sentence.
    """
    tokenized_text = tokenizer.encode(text, add_special_tokens=True)
    
    split_list = text.split('\n\n')
    
    title = split_list[0] # the first one will be the title

    abstract = ''.join([s for s in split_list]).replace('\n', ' ') # taking all the abstract 

    if len(tokenized_text) <= max_split:
        # avoiding to have \n\n for embeddings creation
        return [title + ' ' + abstract]

    
    sentences = sent_tokenize(abstract)
   
    split = []
    current_string = title # starting the parse from the title

    for sentence in sentences:
        tokenization_string = current_string + ' ' + sentence

        if len(tokenizer.encode(tokenization_string, add_special_tokens=True)) > max_split:
            split.append(current_string) # insert the text until the previous sentence
            current_string = sentence
        else:
            current_string = tokenization_string # updatet the sting

    if current_string != "":
        split.append(current_string)

    '''
    #Useful for debugging
    print("Text: ", text)
    print("-"*50)
    for el in split:
        print(el)
        print("*"*50)
    print("-"*50)
    print()
    '''
    return split


def create_embeddings_index(directory_path: str, path_to_save: str, json_wrong_documents: str):
    """
    The function takes in input 3 paths and it returns a folder containing json file with all the infomation of the correct documents

    A document is correct if:
        - its  title has less than 512 token
        - its parse abstracts have less than 512 token

    """
    j = 0
    documents = set() # to avoid to make the process for the same pmid
    auto_id = 1 
    files_number = 0
    for filename in sorted(os.listdir(directory_path)):
        start_time = time.time()
        if filename.endswith(".json"):
            print(f"Starting indexing {filename} ...")
            # Construct the full file path
            file_path = os.path.join(directory_path, filename)
            # Read the JSON file
            with open(file_path, 'r') as file:
                # Initialize an empty list to store dictionaries
                dictionaries = []
                
                # Read the file line by line
                for line in file:
                    # Parse each line as JSON and append it to the list
                    dictionaries.append(json.loads(line))
            
            df = pd.DataFrame(dictionaries)
            
            # Select only the required columns
            df = df[['pmid', 'title', 'abstract', 'journal', 'authors', 'pubdate']]
            
            # Output the file name
            file_documents = []
            
            for i, row in df.iterrows(): 
                pmid = row["pmid"]
                abstract = row["abstract"].strip()  # Strip whitespace from the abstract
                
                # Skip this document if the abstract is empty
                if not abstract:
                    continue
                # skip the documents if it has been just inserted or checked
                if pmid in documents:
                    continue
                

                row['title'] = title_conversion(row['title'])  

                # skip the documents if the title is too large
                if len(tokenizer.encode(row['title'], add_special_tokens=True)) > MAX_SPLIT:
                    row_dict = row.to_dict()
                    row_dict['title_problem'] = True
                    wrong_documents.append(row_dict)
                    continue

                documents.add(pmid)
                
                row['text'] = row['title'] + '\n\n' + row['abstract']
                splitted_documents = split_text(row['text'])

                check = check_results(splitted_documents)

                if check == False:
                    row_dict = row.to_dict()
                    row_dict['title_problem'] = False
                    wrong_documents.append(row_dict)
                    # go to the next documents
                    continue

                for document in splitted_documents:
                    embedding = model.encode(document).tolist() # encoding in a list to save the json
                    doc = {
                        "pmid": pmid,
                        "auto_id": auto_id, # to distinguish different type of abstract for same documents
                        "text": document, # is the parse abstract
                        "total_text": row['text'],  # repeated stuf if the abstract has less 512 token (can be manage for the indexing)
                        "authors": row['authors'],
                        "journal": row['journal'],
                        "pubdate": row['pubdate'],
                        "embedding_abstract": embedding
                        }

                    #file_documents.append({"index": {"_index": index_name, "_id": auto_id}})
                    
                    file_documents.append(doc)
                    auto_id += 1
                    j += 1
                
            
            with open(path_to_save + '/' + filename, "w") as json_file:
                json.dump(file_documents, json_file)
            
            # writing the wrong documents after to each file (safe operation in the case of crash)
            with open(json_wrong_documents, "w") as json_file:
                json.dump(wrong_documents, json_file)

            files_number += 1
            print(f"Processed file: {filename} in {time.time()-start_time}")
           

    print("Total documents inserted = ", j)


print("Staring encoding ...")
create_embeddings_index(path, path_to_save,json_wrong_documents)

