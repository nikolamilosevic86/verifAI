# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 11:24:32 2024

@author: Lenovo
"""

import os
import json
import numpy as np
from tqdm import tqdm  # Import tqdm

"""
def writing_authors(authors_list): 
    #print(authors_list)
    authors_string = ""
    for i, author in enumerate(authors_list):
        if i > 0:
            # inserting comma only if there are more authors
            authors_string += '. '
        authors_string += author['forename'] + ', ' + author['lastname'] + ', ' + author['initials']

    return authors_string
"""


data_directory =  '../../outputNJSON'
output_directory =  '../../outputNJSONextracted' 
# Create output directory if it doesn't exist
if not os.path.exists(output_directory):
    os.makedirs(output_directory)



# Wrap the os.listdir call with tqdm for the progress bar
document_no_information = []
for filename in tqdm(os.listdir(data_directory), desc="Processing files"): #tqdm(os.listdir(data_directory), desc="Processing files")
    
    if filename.endswith('.json'):
        print("Filename ",filename)
        file_path = os.path.join(data_directory, filename)
        output_path = os.path.join(output_directory, filename)

        # Parse the JSON file
        with open(file_path, 'r') as input_file, open(output_path, 'w') as output_file:
            for line in input_file:
                # Parse the JSON line
                data = json.loads(line)
                # Extract the desired fields
                try:
                    extracted_data = {
                        'pmid': data.get('pmid', ''),
                        'title': data.get('title', ''),
                        'abstract': data.get('abstract', ''),
                        'journal': data.get('journal', ''),
                        'authors': data.get('authors', ''),
                        'pubdate': data.get('pubdate', '')
                    }
                    # Write the extracted data to the output file
                    output_file.write(json.dumps(extracted_data) + '\n')
                except:
                    document_no_information.append(data)
                    


print("Number of documents not inserted ", len(document_no_information))


