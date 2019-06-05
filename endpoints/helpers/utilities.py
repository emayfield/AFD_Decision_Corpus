from datetime import datetime, timedelta

class UtilitiesEndpoint:

    def __init__(self, server):
        self.server = server

    def get_timestamps_for_year(self, year):
        try:
            start = datetime(year, 1, 1)
            end = datetime(year+1,1,1)
            return 200, (start.timestamp(), end.timestamp())
        except:
            return 500, None

    def get_text(self, contrib_id):
        try:
            contrib_code = str(contrib_id)[0]
            contrib_text = None 
            if contrib_code == "4":
                code, contrib_text = self.server.votes.get_rationale(contrib_id)
            if contrib_code == "5":
                code, contrib_text = self.server.comments.get_text(contrib_id)
            if contrib_code == "6":
                code, contrib_text = self.server.nominations.get_text(contrib_id)
            if contrib_text != None:
                return 200, contrib_text
            else:
                return 404, None
        except:
            return 500, None
    

    def _match(self, contrib_id, target):
        code = str(contrib_id)[0]
        if code == target:
            return True
        else:
            return False


    def get_tenure(self, contrib_id):
        if self.is_vote(contrib_id):
            return self.server.votes.get_tenure()
        if self.is_comment(contrib_id):
            return self.server.comments.get_tenure()
        if self.is_nomination(contrib_id):
            return self.server.nominations.get_tenure()
        return 404, None

    def put_tenure(self, contrib_id, tenure):
        if self.is_vote(contrib_id):
            return self.server.votes.put_tenure(tenure)
        if self.is_comment(contrib_id):
            return self.server.comments.put_tenure(tenure)
        if self.is_nomination(contrib_id):
            return self.server.nominations.put_tenure(tenure)
        return 404, None

    def get_timestamp(self, contrib_id):
        if self.is_vote(contrib_id):
            return self.server.votes.get_timestamp(contrib_id)
        if self.is_comment(contrib_id):
            return self.server.comments.get_timestamp(contrib_id)
        if self.is_outcome(contrib_id):
            return self.server.outcomes.get_timestamp(contrib_id)
        if self.is_nomination(contrib_id):
            return self.server.nominations.get_timestamp(contrib_id)
        return 404, None


    def get_user_id(self, contrib_id):
        if self.is_vote(contrib_id):
            return self.server.votes.get_user_id(contrib_id)
        if self.is_comment(contrib_id):
            return self.server.comments.get_user_id(contrib_id)
        if self.is_outcome(contrib_id):
            return self.server.outcomes.get_user_id(contrib_id)
        if self.is_nomination(contrib_id):
            return self.server.nominations.get_user_id(contrib_id)
        return 404, None

    def get_discussion_id(self, contrib_id):
        if self.is_vote(contrib_id):
            return self.server.votes.get_discussion_id(contrib_id)
        if self.is_comment(contrib_id):
            return self.server.comments.get_discussion_id(contrib_id)
        if self.is_outcome(contrib_id):
            return self.server.outcomes.get_discussion_id(contrib_id)
        if self.is_nomination(contrib_id):
            return self.server.nominations.get_discussion_id(contrib_id)
        return 404, None

    def is_outcome(self, contrib_id):
        return self._match(contrib_id, "3")

    def is_vote(self, contrib_id):
        return self._match(contrib_id, "4")

    def is_comment(self, contrib_id):
        return self._match(contrib_id, "5")

    def is_nomination(self, contrib_id):
        return self._match(contrib_id, "6")