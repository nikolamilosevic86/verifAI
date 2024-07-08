import pandas as pd
import os
import json
import time
from opensearchpy import OpenSearch
#from preprocessing.abstract_parser import title_conversion

path = '../outputNJSONextracted' #"../outputNJSONextracted"  

host = '127.0.0.1' 
port = 9200
auth = ('admin','admin!') #('admin', 'admin') 

# Create the client with SSL/TLS and hostname verification disabled.

client = OpenSearch(
    hosts = [{'host': host, 'port': port}],
    http_auth = auth,
    use_ssl = True,
    verify_certs = False,
    ssl_assert_hostname = False,
    ssl_show_warn = False,
    timeout=500, 
    max_retries=10
    #connection_class=RequestsHttpConnection 
#    http_compress = True, # enables gzip compression for request bodies
#    use_ssl = False,
#   verify_certs = False,
#    ssl_assert_hostname = False,
#    ssl_show_warn = False
)
print("Connection opened...")

index_name_lexical_pmid = 'medline-faiss-hnsw-lexical-pmid'
index_body = {
 "settings": {
    "index": {
     "refresh_interval" : -1,
     "number_of_shards": 4,
     "number_of_replicas": 0
    }
  },
  "mappings": {
    "properties": {
          "pmid":{"type":"keyword"},
          "full_text":{"type":"text"},
          "journal":{"type":"text", "index": False},
          "pubdate":{"type":"date"},
          "authors": {
                "type": "nested",
                "properties": {
                    "lastname": {"type": "text"},
                    "forename": {"type": "text"},
                    "initials": {"type": "text"},
                    "identifier": {"type": "text"},
                    "affiliation": {"type": "text"},
                }
            }
        }
    }
}

response = client.indices.create(index_name_lexical_pmid, body=index_body)
print(response)


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

    # no title
    if len(title) == 0:
        return title

    # Delete useless white space and substituiting the \n with Whitespace from the title
    title = title.replace('\n',' ').strip() 

    # title[-1] and title[-2] because is same case the square bracket is before the full stop
    if len(title) > 1 and title[0] == '[' and (title[-1] == ']' or title[-2] == ']'): 
      title = remove_outer_square_brackets(title)


    if title[-1] == '.' or title[-1] == '?' or title[-1] == '!':
        return title
    
    # if no marks, we insert the full stop
    return title + '.' 

def create_lexical_pmid_index(directory_path: str, index_name: str, batch_size : int = 500):
    """
    The function takes in input 3 paths and it returns a folder containing json file with all the infomation of the correct documents

    A document is correct if:
        - its  title has less than 512 token
        - its parse abstracts have less than 512 token

    """
    j = 0
    documents = set() # to avoid to make the process for the same pmid
    
    files_number = 0
    
    for filename in sorted(os.listdir(directory_path)):
        
        start_time = time.time()
        if filename.endswith(".json"):
            print(f"Starting parsing {filename} ...")
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
            batch = []
            for i, row in df.iterrows(): 
                pmid = row["pmid"]
                try:
                    abstract = row["abstract"].strip()  # Strip whitespace from the abstract
                except:
                     # abstract Nan
                    continue

                # Skip this document if the abstract is empty
                if not abstract:
                    continue
                # skip the documents if it has been just inserted or checked
                if pmid in documents:
                    continue
                

                row['title'] = title_conversion(row['title'])  

                documents.add(pmid)
                
                row['full_text'] = row['title'] + '\n\n' + row['abstract']
                
                batch.append({"index": {"_index": index_name, "_id": pmid}})
                
                dict_row = row.to_dict()
                # removing title and abstract, the information are stored in full text
                dict_row.pop('title')
                dict_row.pop('abstract')
                
                batch.append(dict_row)
                j += 1
                if len(batch) >= batch_size*2:
                    client.bulk(body=batch, refresh=True)
                    batch = []

            if batch:
                client.bulk(body=batch, refresh=True)
                batch = []    

            files_number += 1
            print(f"Processed file: {filename} in {time.time()-start_time}")
           

    print("Total documents inserted = ", j)


print("Staring indexing ...")
create_lexical_pmid_index(directory_path = path, index_name=index_name_lexical_pmid)

