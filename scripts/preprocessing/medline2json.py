# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.

Unpack medline files and create line separated json files
Store files in outputNJSON folder
"""

from pubmed_parser import parse_medline_xml
import json
import os

data_directory = '../data'   # Change folder path to "../dataUPdate" to extract Medline daily update
output_directory = '../outputNJSON'  # Save NJSON files in a separate directory

# Create output directory if it doesn't exist
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

for filename in os.listdir(data_directory):
    if filename.endswith('.xml.gz'):
        file_path = os.path.join(data_directory, filename)
        json_file_name = filename.replace('.xml.gz', '.json')
        output_path = os.path.join(output_directory, json_file_name)

        # Parse the XML file
        dicts_data = parse_medline_xml(file_path,
                                       year_info_only=False,
                                       nlm_category=False,
                                       author_list=True,
                                       reference_list=False)

        # Save the data as line delimited JSON
        with open(output_path, "w") as outfile:
            for d in dicts_data:
                json.dump(d, outfile)
                outfile.write('\n')
            #json.dump(dicts_data, outfile)

        print(f"Processed and saved: {json_file_name}")