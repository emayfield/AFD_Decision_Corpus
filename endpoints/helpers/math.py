
class MathEndpoint:
    
    """
    Takes a tally and converts it into a probability distribution that sums to 1.
    Params: dict of keys to numeric values.
    Returns: 200, dict of normalized values for each key
        or   500, None if something went wrong.
    """
    def get_normalized_tally(self, tally):
        try:
            total = 0.0
            for key in tally.keys():
                total += tally[key]
            norm_tally = {k:(tally[k]/total) for k in tally.keys()}
            return 200, norm_tally
        except:
            return 500, None

    """
    Params: Two tally dicts to combine
    Returns: 200, Combined tally dicts, where shared keys equal the sum of tallies in each dict.
        or   500, None if something went wrong.
    """
    def get_combined_tally(self, base_tally, new_tally):
        try:
            combined_tally = {}
            for key in base_tally:
                combined_tally[key] = base_tally[key]
            for key in new_tally:
                if key in combined_tally.keys():
                    combined_tally[key] = combined_tally[key] + new_tally[key]
                else:
                    combined_tally[key] = new_tally[key]
            return 200, combined_tally
        except:
            return 500, None