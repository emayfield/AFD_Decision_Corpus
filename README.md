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

* Elements in `Discussion` contain two values:
    - `ID` is a nine-digit integer beginning with the digit `1`.
    - `Title` is a string representing the name of the article being discussed.
        - Sometimes titles contain additional appended information like "*(second nomination)*". Future releases will move this to metadata.

* Elements in `Users` contain two values:
    - `ID` is a nine-digit integer beginning with the digit `2`.
    - `Name` is a string representing the username of an editor. 
        - In many cases, this is an IP address for unregistered users, in either IPv4 or IPv6 format. Future releases will mark unregistered users in metadata. 
        - Some usernames are mildly garbled by signature formatting, though we have taken steps to alleviate this. Username cleaning will continue in future releases.

* Elements in `Outcomes` contain seven values:
    - `ID` is a nine-digit integer beginning with the digit `3`.
    - `Parent` is an integer starting with `1`. This is used as a foreign key linking an outcome to a discussion ID.
    - `User` is an integer starting with `2`. This is used as a foreign key linking an outcome to a user ID.
    - `Timestamp` is an integer value representing the time that a discussion was closed by an administrator with a final outcome and user signature. This has been converted to UNIX timestamp format counting the seconds since January 1, 1970.
    - `Raw` is the bold text from an administrator listing the action item to take from a debate. 
        - This usually falls into one of a very small number of labels, The most common are *Keep* and *Delete*.
        - But there is a very long tail of rarely occuring strings and, in some cases, whole sentences of action items.
    - `Label` is a string of normalized outcome labels that appear in the raw text, sorted and separated by spaces.
        - The goal of this is to convert raw outcome texts into something more easily quantifiable, while acknowledging that 
        - The most common four outcomes are *keep*, *delete*, *merge*, *redirect*, and the modifier *speedy*.
        - Sometimes multiple outcome labels appear at once: *merge delete* for instance.  
        - Heuristic rules in the source code determing how these strings are mapped to specific labels when calculating aggregate statistics. It's mostly a prioritized waterfall of keywords, attempting to merge decisions into "keep"-like and "delete"-like outcomes. For instance, *speedy delete* is merged in with *delete* when performing classification tasks.
        - Also in the source code is a set of rules for converting to a 2-label case with only keep and delete outcomes. Whenever an outcome results in a page not being deleted, those rare outcomes are merged in with *keep*. 
    - `Rationale` is the plaintext of the administrator's text explanation for the outcome that they chose. 
        - This can be (and often is) very short, or in some cases can be a whole paragraph of text.

* Elements in `Contributions` contain six to eight values. Five are shared by all elements, and three are context-specific.
    - `ID` is a nine-digit integer beginning with the digit `4`, `5`, or `6`. 
        - Elements beginning with `4` represent votes for a particular outcome.
        - Elements beginning with `5` represent non-voting comments.
        - Elements beginning with `6` represent nomination statements.
    - `Discussion` is an integer beginning with `1`. 
        - This is a foreign key linking a vote, comment, or nomination to a particular discussion.
    - `Parent` is an integer beginning with `1`. 
        - This is a placeholder value that currently duplicates the value of `Discussion`. 
        - In future releases, this will hold thread structure between votes and comments.
    - `Timestamp` is an integer value representing the time that a comment or vote was signed by its user. This has been converted to UNIX timestamp format counting the seconds since January 1, 1970.
    - `User` is an integer starting with `2`. This is used as a foreign key linking an outcome to a user ID.
    - `Text` is a string that contains the text for nominating statements and comments only. (IDs starting with `5` and `6`). 
        - Votes (IDs starting with `4`) do not contain this field.
    - `Raw` is the bold text from a user listing their vote in the debate
        - This mostly follows the same rules as the definition of raw outcome labels above.
        - This is for votes only (IDs starting with `4`). Comments and nominating statements do not contain this field.
    - `Label` is a string of normalized vote labels that appear in the raw text, sorted and separated by spaces.
        - This mostly follows the same rules as the definition of raw outcome labels above.
        - This is for votes only (IDs starting with `4`). Comments and nominating statements do not contain this field.
    - `Rationale` is the plaintext of a voter's explanation for the vote that they chose. 
        - This is extracted identically to the Text field from comments; they are distinguished only by whether a user voted in this particular contribution to the discussion.


# Publication History

* Elijah Mayfield and Alan W Black. 2019. Analyzing Wikipedia Deletion Debates with a Group Decision-Making Forecast Model. *ACM Conference on Computer-Supported Collaborative Work (CSCW).* **Best Paper Honorable Mention.**
* Elijah Mayfield and Alan W Black. Stance Classification, Outcome Prediction, and Impact Assessment: NLP Tasks for Studying Group Decision-Making. *Workshop on Natural Language Processing for Computational Social Science at the North American Association for Computational Linguistics (NAACL)*.



This data will be cleaned and made more accessible prior to CSCW 2019.
