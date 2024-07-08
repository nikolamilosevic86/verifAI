# verif.ai
No more searches, just verifiably accurate answers.

## Project Description
Verif.ai project aims to address problem of hallucinations in generative large language models and generative search, especially focusing on life sciences domain.
Verif.ai is an AI system designed to verify and document the correctness of AI-generated texts. In the core of the engine is generative search engine, powered by open technologies. However, generative models may hallucinate, and therefore Verif.ai is developing a second model that would check the sources of generative model and flag any misinformation or misinterpretations of source documents. Therefore, make the answer created by generative search engine completly verifiable. The best part is, that we are making it open source, so anyone can use it!


## Installation and start-up

1. Clone the repository
2. Run requirements.txt by running `pip install -r backend/requirements.txt`
3. Download Medline. You can do it by executing `download_medline_data.sh` for core files for the current year and `download_medline_data_update.sh` for Medline current update files.
4. Install Qdrant following the guide [here](https://qdrant.tech/documentation/quick-start/)
5. Run the script: `python medline2json.py` to transform MEDLINE XML files into JSON
6. Run `python json2selected.py` to selects the fields that should be inported into the index
7. Run `python abstarct_parser.py` to concatinate abstract titles and abstracts and splits texts to 512 parts that can be indexed using a transformer model
8. Run `python embeddings_creation.py` to create embeddings.
9. Run `python scripts/indexing_qdrant.py` to create qdrant index. Make sure to point to the right folder created in the previous step and to the qdrant instance. 
10. Install OpenSearch following the guide [here](https://opensearch.org/docs/latest/install-and-configure/install-opensearch/index/)
11. Create OpenSearch index by running `python scripts/indexing_lexical_pmid.py`. Make sure to configure access to the OpenSearch and point the path variable to the folder created by json2selected script.
12. Set up system variables that are needed for the project:
```
export DBNAME=db_name
export USER_DB=db_username
export PASSWORD_DB=db_password
export HOST_DB=db_host_name

export VERIFAI_IP=ip_address_of_machines_with_qdrant_and_opensearch
export VERIFAI_USER=user_name_open_search
export VERIFAI_PASSWORD=password_open_search
export VERIFAI_PORT=port_open_search
export QDRANT_PORT=port_qdrant
```
13. Run backend by running `python backend/main.py`
14. Install React by following (this guide)[https://www.freecodecamp.org/news/how-to-install-react-a-step-by-step-guide/]
15. Run `npm build`
16. Run frontend by running `npm start` in client-gui/verifai-ui

## Collaborators and contributions

Currently, two institutions are the main drivers of this project, namely Bayer A.G and Institute for Artificial Intelligence Research and Development of Serbia. Current contrbiutors are by institutions
* Bayer A.G.
  * Nikola Milosevic
  * Lorenzo Cassano
* Institute for Artificial Intelligence Research and Development of Serbia:
  * Adela Ljajic
  * Milos Kosprdic
  * Bojana Basaragin
  * Darija Medvecki
  * Angela Pupovac

We welcome contribution to this project by anyone interested in participating. This is an open source project under AGPL license. In order to prevent any legal issues, before sending the first pull request, we ask potential contributors to sign [Individual Contributor Agreement](https://github.com/nikolamilosevic86/verif.ai/blob/main/Legal/Individual%20Contributor%20Agreement%20Verifai_fillable.pdf) and send to us via email (verif.ai.project@gmail.com).

## Citations

* [Košprdić, M., Ljajić, A., Bašaragin, B., Medvecki, D., & Milošević, N. "Verif. ai: Towards an Open-Source Scientific Generative Question-Answering System with Referenced and Verifiable Answers." The Sixteenth International Conference on Evolving Internet INTERNET 2024 (2024).](https://arxiv.org/pdf/2402.18589.pdf)

## Funding 

This project was in September 2023 funded by NGI Search project of the European Union. Views and opinions expressed are however those of the author(s) only and do not necessarily reflect those of the European Union or European Commission. Neither the European Union nor the granting authority can be held responsible for them. Funded within the framework of the NGI Search project under grant agreement No 101069364
