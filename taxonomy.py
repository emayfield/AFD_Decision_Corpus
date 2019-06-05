
class Taxonomy:
    def __init__(self):
        self.links, self.tiers, self.alias = self.rigorous_taxonomy()

    # Taxonomy produced by this method is a data structure:
    #
    # links is a dict.
    # Key: category name
    # Value: Dict consisting of:
    #        Key: Page
    #        Value: Dict consisting of:
    #               Key: Subsection name
    #               Value: 1
    #
    # tiers is a dict
    # Key: page name or link name
    # Value: tier value from:
    #   *: Policy
    #   +: Guideline
    #   ^: Essay
    #   @: Biographic Notability
    #
    # alias is a dict
    # Key: link name
    # Value: normalized alias for that link.
    def rigorous_taxonomy(self):
        links = {}
        tiers = {}
        alias = {}

        taxonomy_file = open("taxonomy.txt", "r")
        current_category = None
        current_page = None
        current_link = None
        current_alias = None
        current_tier = None
        for line in taxonomy_file:
            input = line.strip().lower()
            if input.startswith("#"):
                pass
            elif input.startswith("==="):
                current_category = input.replace("===","").strip()
                links[current_category] = {}
            elif input.startswith("*") or input.startswith("+") or input.startswith("@") or input.startswith("^"):
                meaning_map = {
                    "*":"Policy",
                    "+":"Guideline",
                    "^":"Essay",
                    "@":"Notability Guideline"
                }
                current_tier = meaning_map[input[:1]]
                current_page = input[1:].strip()
                if current_alias is None:
                    current_alias = current_page
                links[current_category][current_page] = {}
                tiers[current_page] = current_tier
                alias[current_page] = current_alias
            elif input.startswith("-") or input.startswith("="):
                current_alias = None
                current_link = None
                # Occasionally, guideline pages have policies in specific subsections only.
                # Notably, this happens in the signatures page.
                if input.startswith("-") and (("*" in input) or ("+" in input)):
                    if "*" in input:
                        current_tier = "Policy"
                    if "+" in input:
                        current_tier = "Guideline"
                if input.startswith("="):
                    current_page = None
            elif len(input) > 0:
                current_link = input
                if current_alias is None:
                    current_alias = current_link
                links[current_category][current_page][current_link] = 1
                tiers[current_link] = current_tier
                alias[current_link] = current_alias
        return links, tiers, alias

    def abstract(self, potential_link, abstraction):
        for cat in self.links.keys():
            for page in self.links[cat].keys():
                found = None
                if page == potential_link:
                    found = page
                else:
                    for link in self.links[cat][page].keys():
                        if link == potential_link:
                            found = link
                if found is not None:          
                    if(abstraction == "link"):
                        return found
                    elif(abstraction == "page"):
                        return page
                    elif(abstraction == "category"):
                        return cat
                    elif(abstraction == "subpage"):
                        return self.alias[found]
                    elif(abstraction == "formality"):
                        return self.tiers[found]

                                