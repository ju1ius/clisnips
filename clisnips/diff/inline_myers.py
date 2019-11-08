from .myers import MyersSequenceMatcher


class InlineMyersSequenceMatcher(MyersSequenceMatcher):

    def preprocess_discard_nonmatching_lines(self, a, b):

        if len(a) <= 2 and len(b) <= 2:
            self.a_index = []
            self.b_index = []
            return a, b

        def index_matching_kmers(a, b):
            a_set = set([a[i:i + 3] for i in range(len(a) - 2)])
            matches, index = [], []
            next_possible_match = 0
            # Start from where we can get a valid triple
            for i in range(2, len(b)):
                if b[i - 2:i + 1] not in a_set:
                    continue
                # Make sure we don't re-record matches from overlapping kmers
                for j in range(max(next_possible_match, i - 2), i + 1):
                    matches.append(b[j])
                    index.append(j)
                next_possible_match = i + 1
            return matches, index

        indexed_b, self.b_index = index_matching_kmers(a, b)
        indexed_a, self.a_index = index_matching_kmers(b, a)

        # We only use the optimised result if it's worthwhile. The constant
        # represents a heuristic of how many lines constitute 'worthwhile'.
        self.lines_discarded = (len(b) - len(indexed_b) > 10 or
                                len(a) - len(indexed_a) > 10)
        if self.lines_discarded:
            a = indexed_a
            b = indexed_b
        return a, b
