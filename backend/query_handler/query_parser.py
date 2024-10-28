from concurrent.futures import ThreadPoolExecutor
from datetime import timezone

from nltk.tokenize import word_tokenize
from datetime import datetime
from qdrant_client.http import models
from utils import parse_date
import dateutil

class QueryProcessor:
    def __init__(self, index_lexical:str = "medline-faiss-hnsw-lexical-pmid", index_name_semantic:str ="medline-faiss-hnsw",
                model=None, lexical_client=None, semantic_client=None, rescore = True, stopwords=set([])):
        
        self.index_lexical_name = index_lexical
        self.index_name_semantic = index_name_semantic
        self.model = model
        
        self.lexical_client = lexical_client
        self.semantic_client = semantic_client
        self.stop_words = stopwords
        
        self.rescore = rescore
    
    def set_rescore(self, rescore: bool):
        self.rescore = rescore

    def preprocess_query(self, query_str: str) -> str:
        return ' '.join([word for word in word_tokenize(query_str) if word.lower() not in self.stop_words])
      
    
    def reorder_pmid(self, retrived_documents: list) -> set:
        pmid_scores = {}
        
        # Iterate through the set data
        for _, value in retrived_documents.items():
            if value['pmid'] != "":
                pmid = value['pmid']
            else:
                pmid = value['location']
            score = value['score']
            
            # Check if pmid already exists in the dictionary
            if pmid in pmid_scores:
                pmid_scores[pmid] += score
            else:
                pmid_scores[pmid] = score
           
        return pmid_scores
    
    
    
    def lexical_query(self, query_str: str, pubdate_filter_lte: str, pubdate_filter_gte:str, limit: int = 10) -> set:
        if self.lexical_client == None:
            raise ValueError("No Lexical client defined")
        
        query = {
            "size": limit,
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query_str,
                                "fields": ["full_text"]
                            }
                        },
                        {
                            "range": {
                                "pubdate": {
                                    "gte": pubdate_filter_gte,
                                    "lte": pubdate_filter_lte
                                }
                            }
                        }
                    ]
                }
            }
        }
        
        results = self.lexical_client.search(index=self.index_lexical_name, body=query) 
        
        retrieved_documents = {}
        max_score = results['hits']['max_score']
        for hit in results["hits"]["hits"]:
            location = ""
            pmid = ""
            if 'pmid' not in hit["_source"].keys():
                location = hit["_source"]["location"]
            else:
                pmid = hit["_source"]["pmid"]
            score = hit["_score"] / max_score
            if pmid != "":
                retrieved_documents[pmid] = score
            else:
                retrieved_documents[location] = score
            
        return retrieved_documents #adjust the return 

    def semantic_query(self, query: str, limit: int = 10) -> set:
        #print("semantic = ",query)
        if self.semantic_client == None:
            raise ValueError("No Semantic client defined")
        if self.model == None:
            raise ValueError("No model defined")
        
        query_vector = self.model.encode(query).tolist()
    
        search_params=models.SearchParams(
            quantization=models.QuantizationSearchParams(rescore=self.rescore)
            )
        results = self.semantic_client.search(collection_name=self.index_name_semantic,query_vector=query_vector,search_params=search_params, limit=limit)
        
        retrived_documents = {}
        max_score = None
        for i,document in enumerate(results):
            location = ""
            if 'pmid' not in document.payload.keys():
                location = document.payload['metadata']['location']
                pmid = ""
            else:
                pmid = document.payload['pmid']
                location = ""
            score = document.score
            if i == 0:
                # first score is the max
                max_score = score
            retrived_documents[document.id] = { 'pmid': pmid,'location':location, 'score': round(score / max_score, 5) }

        retrived_documents = self.reorder_pmid(retrived_documents)
        
        return retrived_documents
    

    def hybrid_query(self, query_lexical:str, query_semantic: str,pubdate_filter_lte:str, pubdate_filter_gte:str,
                    lex_parameter: float = 0.5, semantic_parameter: float = 0.5, limit: int = 10) -> set:
        if (lex_parameter + semantic_parameter) > 1:
            raise ValueError("Uncorrect parameters for Hybrid Queries")

        with ThreadPoolExecutor() as executor:
            thread_lexical = executor.submit(self.lexical_query,  query_lexical,pubdate_filter_lte, pubdate_filter_gte, limit)
            thread_semantic = executor.submit(self.semantic_query, query_semantic, limit)
        
        lexical_results = thread_lexical.result()
        semantic_results = thread_semantic.result()
        
        #lexical_results = self.lexical_query(query_lexical, limit = limit) 
        #semantic_results = self.semantic_query(query_semantic, limit)
        max_score = 0
        retrived_documents = {}
        
        for lex_pmid in lexical_results:
            score = lexical_results[lex_pmid] * lex_parameter
            if lex_pmid in semantic_results:
                score += semantic_results[lex_pmid] * semantic_parameter

            retrived_documents[lex_pmid] = score
            max_score = max(max_score, score)
            

        for semantic_pmid in semantic_results:
            if semantic_pmid not in lexical_results:
                score = semantic_results[semantic_pmid] * semantic_parameter
                retrived_documents[semantic_pmid] = score
                max_score = max(max_score, score)
                
        return retrived_documents # just to have a starting point


    def execute_query(self, query_str: str, query_type: str ='lexical',lex_parameter: float = 0.5, semantic_parameter: float = 0.5,
                      limit:int = 10, pubdate_filter_lte :str = "2100-01-01",
                      pubdate_filter_gte :str = "1900-01-01",stopwords_preprocessing: bool = True) -> list:
   
        text_query = self.preprocess_query(query_str) if stopwords_preprocessing else query_str
        
        if query_type == 'lexical':
            results = self.lexical_query(text_query, pubdate_filter_lte, pubdate_filter_gte, limit=limit) 
        
        elif query_type == 'semantic':
            results = self.semantic_query(query_str, limit=limit)

        elif query_type == 'hybrid':
            results = self.hybrid_query(text_query, query_str, pubdate_filter_lte, pubdate_filter_gte,
                                        lex_parameter, semantic_parameter, limit=limit)
        else:
            raise ValueError("Invalid query type specified. Choose 'lexical', 'semantic', or 'hybrid'.")
        
        
        document_retrived = sorted(results.items(), key=lambda x: x[1], reverse=True)
        

        date_lte = parse_date(pubdate_filter_lte)
        date_gte = parse_date(pubdate_filter_gte)
        document_retrived = self.process_results(document_retrived, limit, date_lte, date_gte)
        
        # should be cases using the date, where the systems does not find anything
        if document_retrived == []:
            raise Exception(f"No document retrived for {query_str} using {query_type} search")

        return document_retrived
    

    def process_results(self, results: list, limit:int, date_lte: datetime, date_gte: datetime) -> list:
        retrieved_documents = []
        for i,element in enumerate(results):
            
            pmid,_ = element
            if pmid == '':
                continue
            if isinstance(pmid, int):
                query = {
                        "query": {
                            "term": {
                            "pmid": int(pmid)
                            }
                        }
                    }
            else:
                location = pmid
                pmid = ""
                query = {
                        "query": {
                            "match_phrase": {
                            "location": location
                            }
                        }
                    }

            results = self.lexical_client.search(index=self.index_lexical_name, body=query) 
            full_text = results['hits']['hits'][0]["_source"]['full_text']
            date_string = results['hits']['hits'][0]["_source"]['pubdate']
            location = results['hits']['hits'][0]["_source"]['location']
            
            date = parse_date(date_string)
            date = date.replace(tzinfo=None)
            
            if date_gte <= date and date <= date_lte:
                retrieved_documents.append({
                    "pmid": pmid,
                    "location": location,
                    "text": full_text,
                    "pubdate": date
                    })

            if i == limit-1:
                break
        
        return retrieved_documents