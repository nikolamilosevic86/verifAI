#!/bin/bash

# downloads all MEDLINE/Pubmed citations in the annual baseline.

		for i in $(seq 1 1219); do
    fname="1"
    if ((i < 10)); then
        fname="ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline/pubmed24n000$i.xml.gz"
    elif ((i < 100)); then
        fname="ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline/pubmed24n00$i.xml.gz"
    elif ((i < 1000)); then
        fname="ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline/pubmed24n0$i.xml.gz"
    elif ((i < 10000)); then
        fname="ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline/pubmed24n$i.xml.gz"

    fi
    echo $fname;
    wget $fname;
    sleep 2;
done
