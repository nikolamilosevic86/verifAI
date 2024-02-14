#!/bin/bash

# downloads all MEDLINE/Pubmed citations in daily update 

		for i in $(seq 1220 1289); do
    fname="1"
    if ((i < 1000)); then
        fname="ftp://ftp.ncbi.nlm.nih.gov/pubmed/updatefiles/pubmed24n0$i.xml.gz"
    elif ((i < 10000)); then
        fname="ftp://ftp.ncbi.nlm.nih.gov/pubmed/updatefiles/pubmed24n$i.xml.gz"

    fi
    echo $fname;
    wget $fname;
    sleep 2;
done
