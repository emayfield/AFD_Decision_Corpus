import json
from taxonomy import Taxonomy
import re

def shrink_corpus(filename, file_out, modulo=20, offset=2, min=0, max=500000):

    test_min = 100000000+min
    test_max = 100000000+max
    corpus_file = open(filename, "r")
    corpus_json = json.loads(corpus_file.read())
    discs = corpus_json["Discussions"]
    users = corpus_json["Users"]
    outcomes = corpus_json["Outcomes"]
    contribs = corpus_json["Contributions"]

    citations = find_cites(contribs)

    out_discs = []
    out_outcomes = []
    out_contribs = []
    print("{} {} {}".format(len(discs), len(outcomes), len(contribs)))
    for disc in discs:
        disc_id = disc["ID"]
        if test_min <= disc_id < test_max:
#        if (int(disc_id)+offset) % modulo == 0:
#            print(disc_id)
            out_discs.append(disc)
    for outcome in outcomes:
        disc_id = outcome["Parent"]
#        if (int(disc_id)+offset) % modulo == 0:
        if test_min <= disc_id < test_max:
#            print(outcome["ID"])
            out_outcomes.append(outcome)
    for contrib in contribs:
        disc_id = contrib["Discussion"]
#        if (int(disc_id)+offset) % modulo == 0:
        if test_min <= disc_id < test_max:
#            print(contrib["ID"])
#            if "Rationale" in contrib.keys():
#                contrib["Rationale"] = ""
#            if "Text" in contrib.keys():
#                contrib["Text"] = ""
            out_contribs.append(contrib)
    out_json = {"Users":users, "Discussions":out_discs, "Outcomes":out_outcomes, "Contributions":out_contribs, "Citations":citations}
    corpus_out = open(file_out, "w")
    print(json.dumps(out_json), file=corpus_out)

def find_cites(contribs):
    tax = Taxonomy()
    successes = 0
    failures = 0
    citations = []
    for contrib in contribs:
        row = None
        if "Rationale" in contrib.keys():
            row = contrib["Rationale"]
        if "Text" in contrib.keys():
            row = contrib["Text"]
        if row is not None:
            cites = search_for_citations(tax, row)
            entry = {"ID":contrib["ID"], "Citations":cites}
            citations.append(entry)
            successes += 1
        else:
            failures += 1
    return citations


def sample_corpus(count, min=0, max=500000):
    test_min = 100000000+min
    test_max = 100000000+max
    filename = ""
    corpus_file = open(filename, "r")
    corpus_json = json.loads(corpus_file.read())
    discs = corpus_json["Discussions"]
    users = corpus_json["Users"]
    outcomes = corpus_json["Outcomes"]
    contribs = corpus_json["Contributions"]

    out_discs = []
    out_outcomes = []
    out_contribs = []
    print("{} {} {}".format(len(discs), len(outcomes), len(contribs)))
    for disc in discs:
        disc_id = disc["ID"]
        if test_min <= disc_id < test_max:
#            print(disc_id)
            out_discs.append(disc)


# Called when we have found a timestamped line, to register all of the citations to 
# policy that are made within that line.
def search_for_citations(taxonomy, row):
    citations_found, links = regex_citations(row, taxonomy)
    flat_citations = []
    if citations_found:
        for citation in links:
            simple, flattened_citation = citation_flatten(citation)
            flattened_citation = citation if not simple else flattened_citation
            flat_citations.append(flattened_citation)
        flat_citations = flat_citations
    return flat_citations
            

def regex_citations(line, tax, include_signatures = True):
    if not include_signatures:
        signature_pattern = "\[\[User:"
        signatures = re.finditer(signature_pattern, line)
        starts = [s.start() for s in signatures]
        if len(starts) > 0:
            line = line[0:starts[-1]]
    links_pattern = "\[\[([^\]]+)\]\]"
    links = re.findall(links_pattern, line)
    citations = []
    for link in links:
        m = None
        namespace_pattern = "(wp|wikipedia):([^\|]+)"
        p = re.compile(namespace_pattern)
        m = p.search(link.lower())
        if m is not None:
            potential_link = m.group(2).strip()
            if potential_link in tax.alias.keys():
                # use for "formality" experiments
                #collapsed_citation = tax.alias[potential_link]
                # use for "alias" experiments
                # collapsed_citation = potential_link
                # use by default
                collapsed_citation = tax.abstract(potential_link, "page")
                citations.append(collapsed_citation)
    if len(citations) > 0:
        return True, citations
    else:
        return False, None

collapsible_citations = {
    "old vfd": "(votes|articles).for.deletion/",
    "deletion sorting": "wikiproject deletion sorting"
}

def citation_flatten(cite):
    option_keywords = []
    for o in collapsible_citations.keys():
        p = re.compile(collapsible_citations[o])
        m = p.search(cite)
        if m is not None:
            option_keywords.append(o)
    if(len(option_keywords) > 0):
        keywords = " ".join(sorted(option_keywords))
        result = "[{}]".format(keywords)
        return True, result
    else:
        return False, cite

if __name__=="__main__":
#    for i in range(2,21):
#    print("shrinking {}".format(i))
    shrink_corpus("afd_2019_full.json", "afd_2019_full_policies.json")