Tasks

1) Shortlist of plant traits
2) Match plants to scientific names and get plant list
    a) This can apparently be done via ncbi's taxonomy database and querying from bash. Probably just need to figure out how it works and a simple bash script. Looks like a job for you... 
    Docs: https://www.ncbi.nlm.nih.gov/books/NBK179288/#chapter6.Searching_and_Filtering

    sudo apt install ncbi-entrez-direct
    esearch -db taxonomy -query "Pinus"

3) Make new request for data. 
