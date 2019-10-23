# Wikipedia Deletion Debates Corpus

This dataset is a labeled and structured JSON replica of all debates in Wikipedia's *Articles for Deletion* editor debates from January 1, 2005 to December 31, 2018. The total size of the dataset is a bit over 400k total debates, with over 3 million total votes and comments.

# Version History and Download Links:
* Up-To-Date
    - Corpus files are unchanged from version 1.0.
    - The github branch `cscw_cleanup` contains the most recent version of the code for interacting with the corpus. Changes include:
        - BERT representation extraction has been moved to the `pytorch-transformers` library provided by HuggingFace. Previous versions used the `bert-as-service` library released by Han Xiao.

* 1.0: https://drive.google.com/open?id=180rKdJeEOVTVanNwGd8dtbsdSg7zR536
    - This is the first full-fledged version of the corpus, used in our CSCW 2019 paper.
    - The github branch `cscw_checkpoint` contains a snapshot of code used for all CSCW 2019 results.

* 0.1: https://drive.google.com/open?id=137CQIvN4mRRnWlUNpHgfnVxyfeR2ZE5t
    - This is the preliminary version of the corpus, used in our NAACL 2019 workshop paper

# Data Format

The corpus is divided into 20 files each containing a stratified subset of 5% of discussions, or approximately 20,000 discussions in each data file. Each of these subsets contains a single large JSON object with four top-level child elements: `Discussions`, `Users`, `Outcomes`, and `Contributions`. Each of the four, in turn, contains thousands of child elements of its own.

Each subchild of these four top-level categories represents a single entity in the corpus. Each entity has a unique nine-digit ID. The schema for each entity type is as follows:

* `Discussion` contain two values:
    - ``ID`` is a nine-digit integer beginning with the digit `1`.
    - ``Title`` is a string representing the name of the article being discussed, sometimes with additional appended information like *(second nomination)*.

# Publication History

* Elijah Mayfield and Alan W Black. 2019. Analyzing Wikipedia Deletion Debates with a Group Decision-Making Forecast Model. *ACM Conference on Computer-Supported Collaborative Work (CSCW).* **Best Paper Honorable Mention.**
* Elijah Mayfield and Alan W Black. Stance Classification, Outcome Prediction, and Impact Assessment: NLP Tasks for Studying Group Decision-Making. *Workshop on Natural Language Processing for Computational Social Science at the North American Association for Computational Linguistics (NAACL)*.



This data will be cleaned and made more accessible prior to CSCW 2019.
