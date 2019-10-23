class UserEndpoint():

    def __init__(self, server):
        self.users = {}
        self.server = server

    """
    Params: JSON representation of a user.
    Returns: 201, ID of the created User object
        or   500, None if something went wrong.
    """
    def post_user(self, user_json):
        user = User(user_json)
        try:
            user_id = user.id
            self.users[user_id] = user
            return 201, user_id
        except:
            return 500, None

    """
    Params: User ID to access and ID of a contribution by that user
    Returns: 200, same user ID if the contribution ID was successfully stored.
        or   500, None if something went wrong.
    """
    def put_contribution_id(self, user_id, contribution_id, timestamp):
        try:
            if user_id in self.users.keys():
                user = self.users[user_id]
                tenure = len(user.contributions)
                user.contributions.append((contribution_id, timestamp))
#                user.contributions = list(sorted(user.contributions, key=lambda x:x[1]))
                self.users[user_id] = user
                return 200, user_id
            else:
                return 404, None
        except:
            return 500, None

    """
    Call after corpus is loaded. Sorts all users' contribution lists in chronological order.
    """
    def put_sort_contributions(self):
        try:
            for user_id in self.users.keys():
                user = self.users[user_id]
                user.contributions = list(sorted(user.contributions, key=lambda x:x[1]))
                for i, c in enumerate(user.contributions):
                    self.server.util.put_tenure(c, i)
            num_users = len(self.users.keys())
            print("Sorted {} users".format(num_users))
            return 200, num_users
        except:
            return 500, None

    """
    Params: None
    Returns: 200, List of all known user IDs in the corpus
        or   500, None if something went wrong.
    """
    def get_all(self):
        try:
            return 200, self.users.keys()
        except:
            return 500, None

    """
    Params: User ID to search for
    Returns: 200, One User object matching the given ID
        or   404, None if no user with that ID is found
        or   500, None if something else went wrong.
    """
    def get_by_id(self, user_id):
        try:
            if user_id in self.users.keys():
                return 200, self.users[user_id]
            else:
                return 404, None
        except:
            return 500, None

    """
    Params: User ID (int) to search for
    Returns: 200, String of the ID's username
        or   404, None if that user ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_name(self, user_id):
        try:
            if user_id in self.users.keys():
                return 200, self.users[user_id].name
            else:
                return 404, None
        except:
            return 500, None
        
    """
    Params: username (string) to search for
    Returns: 200, int of the user ID for the input name
        or   404, None if that username does not exist.
        or   500, None if something else went wrong.
    """
    def get_id_by_name(self, input_name):
        try:
            for id in self.users.keys():
                test_name = self.get_name(id)
                if test_name == input_name:
                    return 200, id
            return 404, None
        except:
            return 500, None

    """
    Params: Minimum and maximum number of user contributions to qualify for a cohort.
    Returns: 200, list of user IDs with at least min contributions and fewer than max contributions.
        or   500, None if something else went wrong.
    """
    def get_users_by_tenure(self, min=0, max=999999999):
        try:
            tenure_list = list(filter(lambda x: min <= len(self.users[x].contributions) < max, self.users.keys()))
            return 200, tenure_list
        except:
            return 500, None
    
    """
    Params: User ID to look up and index n (zero-based int)
    Returns: 200, nth contribution by that user if at least n+1 contributions have been made.
        or   202, None if user has made exactly n contributions (dropout code)
        or   404, None if user ID does not exist or n > number of contributions made
        or   500, None if something else went wrong.
    """
    def get_nth_contribution(self, user_id, index):
        try:
            code, user = self.get_by_id(user_id)
            if code == 200:
                contribs = user.contributions
                if index < len(contribs):
                    return 200, contribs[index][0]
                elif index == len(contribs):
                    return 202, None
                else:
                    return 404, None
            else:
                return code, None
        except:
            return 500, None


    """
    Params: User ID (int) to search for
    Returns: 200, list of all contributions made by this user.
        or   404, None if that user ID does not exist.
        or   500, None if something else went wrong.
    """
    def get_contributions(self, user_id):
        try:
            code, user = self.get_by_id(user_id)
            if code == 200:
                contribs = user.contributions
                return 200, [c[0] for c in contribs]
            else:
                return code, None
        except:
            return 500, None

    """
    Params: User ID to check
    Returns: 200, (dict) counts of outcomes, votes, comments, and nominations from that user.
        or   500, None if something went wrong.
    """
    def get_participation_breakdown(self, user_id):
        try:
            code, contrib_ids = self.get_contributions(user_id)
            breakdown = {
                "Outcomes":0,
                "Votes":0,
                "Comments":0,
                "Nominations":0
            }
            code_map = {
                "3":"Outcomes",
                "4":"Votes",
                "5":"Comments",
                "6":"Nominations"
            }
            for c in contrib_ids:
                key = code_map[str(c)[0]]
                breakdown[key] = breakdown[key]+1
            return 200, breakdown
        except:
            return 500, None

    """
    Params: User ID to look up, Contribution ID to look up for that user
    Returns: 200, N (zero-based int) where the contribution is that user's Nth total AfD vote,comment,outcome,nomination
        or   404, None if that user ID does not exist or that contribution ID wasn't from that user.
        or   500, None if something else went wrong.
    """
    def get_tenure_at_contribution(self, user_id, contrib_id):
        try:
            code, user = self.get_by_id(user_id)
            if code == 200:
                for i, c_tuple in enumerate(user.contributions):
                    if c_tuple[0] == contrib_id:
                        return 200, i
            else:
                return code, None
        except:
            return 500, None

      
    def put_demographics(self, user_id, demo_map):
        try:
            code, user = self.get_by_id(user_id)
            if "gender" in demo_map:
                gender = demo_map["gender"]
                user.gender = gender
            if "signup" in demo_map:
                signup = demo_map["signup"]
                user.signup = signup
            if "editcount" in demo_map:
                edits = demo_map["editcount"]
                user.edits = edits
            return 200, user_id
        except:
            return 500, None
            
    def get_edit_count(self, user_id):
        try:
            code, user = self.get_by_id(user_id)
            if code == 200:
                edits = user.edits
                if edits:
                    return 200, edits
            return code, None
        except:
            return 500, None

    def get_gender(self, user_id):
        try:
            code, user = self.get_by_id(user_id)
            if code == 200:
                gender = user.gender
                if gender:
                    return 200, gender
            return code, None
        except:
            return 500, None
            
    def get_signup(self, user_id):
        try:
            code, user = self.get_by_id(user_id)
            if code == 200:
                signup = user.signup
                if signup:
                    return 200, signup
            return code, None
        except:
            return 500, None 
        
    def get_first_contribution(self, user_id):
        try:
            code, user = self.get_by_id(user_id)
            if code == 200 and len(user.contributions) > 0:
                first_contrib_id, first_contrib_timestamp = user.contributions[0]
                if first_contrib_id:
                    return 200, first_contrib_id
            return 404, None
        except:
            return 500, None

    def put_first_discussion(self, user_id, disc_id):
        try:
            code, user = self.get_by_id(user_id)
            if code == 200:
                user.first_discussion = disc_id
                self.users[user_id] = user
                return 200, user_id
            return code, None
        except:
            return 500, None
    
    def get_first_discussion(self, user_id):
        try:
            code, user = self.get_by_id(user_id)
            if code == 200 and user.first_discussion is not None:
                return 200, user.first_discussion
            return 404, None
        except:
            return 500, None

    def is_registered(self, user_id):
        try:
            code, user = self.get_by_id(user_id)
            if code == 200 and user.signup is not None:
                registered = user.signup > -1
                return 200, registered
            return code, None
        except:
            return 500, None

class User:
    def __init__(self, user_json):
        self.id = -1
        self.name = None
        self.gender = "unknown"
        self.signup = None
        self.edits = None
        self.contributions = []
        self.first_discussion = None
        if "ID" in user_json.keys():
            self.id = user_json["ID"]
        if "Name" in user_json.keys():
            self.name = user_json["Name"]