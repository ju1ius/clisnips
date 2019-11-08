from collections import namedtuple
from difflib import SequenceMatcher

DiffChunk = namedtuple('DiffChunk', 'tag, start_a, end_a, start_b, end_b')


def find_common_prefix(a, b):
    if not a or not b:
        return 0
    if a[0] == b[0]:
        pointer_max = min(len(a), len(b))
        pointer_mid = pointer_max
        pointer_min = 0
        while pointer_min < pointer_mid:
            if a[pointer_min:pointer_mid] == b[pointer_min:pointer_mid]:
                pointer_min = pointer_mid
            else:
                pointer_max = pointer_mid
            pointer_mid = int((pointer_max - pointer_min) // 2 + pointer_min)
        return pointer_mid
    return 0


def find_common_suffix(a, b):
    if not a or not b:
        return 0
    if a[-1] == b[-1]:
        pointer_max = min(len(a), len(b))
        pointer_mid = pointer_max
        pointer_min = 0
        while pointer_min < pointer_mid:
            a_tail = a[-pointer_mid:len(a) - pointer_min]
            b_tail = b[-pointer_mid:len(b) - pointer_min]
            if a_tail == b_tail:
                pointer_min = pointer_mid
            else:
                pointer_max = pointer_mid
            pointer_mid = int((pointer_max - pointer_min) // 2 + pointer_min)
        return pointer_mid
    return 0


class MyersSequenceMatcher(SequenceMatcher):

    def __init__(self, isjunk=None, a='', b=''):
        if isjunk is not None:
            raise NotImplementedError('is_junk is not supported yet')
        super().__init__()
        self.a = a
        self.b = b
        self.matching_blocks = self.opcodes = None
        self.a_index = []
        self.b_index = []
        self.common_prefix = self.common_suffix = 0
        self.lines_discarded = False

    def set_seq2(self, b):
        # we need to override since we don't support is_junk
        # and the original methods call self.__chain_b()
        # which uses self.is_junk
        if b is self.b:
            return
        self.b = b
        self.matching_blocks = self.opcodes = None

    def get_matching_blocks(self):
        if self.matching_blocks is None:
            for i in self.initialise():
                pass
        return self.matching_blocks

    def get_opcodes(self):
        opcodes = SequenceMatcher.get_opcodes(self)
        return [DiffChunk._make(chunk) for chunk in opcodes]

    def get_difference_opcodes(self):
        return [chunk for chunk in self.get_opcodes() if chunk.tag != 'equal']

    def preprocess_remove_prefix_suffix(self, a, b):
        # remove common prefix and common suffix
        self.common_prefix = self.common_suffix = 0
        self.common_prefix = find_common_prefix(a, b)
        if self.common_prefix > 0:
            a = a[self.common_prefix:]
            b = b[self.common_prefix:]

        if len(a) > 0 and len(b) > 0:
            self.common_suffix = find_common_suffix(a, b)
            if self.common_suffix > 0:
                a = a[:len(a) - self.common_suffix]
                b = b[:len(b) - self.common_suffix]
        return a, b

    def preprocess_discard_nonmatching_lines(self, a, b):
        # discard lines that do not match any line from the other file
        if len(a) == 0 or len(b) == 0:
            self.a_index = []
            self.b_index = []
            return a, b

        def index_matching(a, b):
            aset = frozenset(a)
            matches, index = [], []
            for i, line in enumerate(b):
                if line in aset:
                    matches.append(line)
                    index.append(i)
            return matches, index

        indexed_b, self.b_index = index_matching(a, b)
        indexed_a, self.a_index = index_matching(b, a)

        # We only use the optimised result if it's worthwhile. The constant
        # represents a heuristic of how many lines constitute 'worthwhile'.
        self.lines_discarded = (len(b) - len(indexed_b) > 10 or
                                len(a) - len(indexed_a) > 10)
        if self.lines_discarded:
            a = indexed_a
            b = indexed_b
        return a, b

    def preprocess(self):
        """
        Pre-processing optimizations:
        1) remove common prefix and common suffix
        2) remove lines that do not match
        """
        a, b = self.preprocess_remove_prefix_suffix(self.a, self.b)
        return self.preprocess_discard_nonmatching_lines(a, b)

    def postprocess(self):
        """
        Perform some post-processing cleanup to reduce 'chaff' and make
        the result more human-readable. Since Myers diff is a greedy
        algorithm backward scanning of matching chunks might reveal
        some smaller chunks that can be combined together.
        """
        mb = [self.matching_blocks[-1]]
        i = len(self.matching_blocks) - 2
        while i >= 0:
            cur_a, cur_b, cur_len = self.matching_blocks[i]
            i -= 1
            while i >= 0:
                prev_a, prev_b, prev_len = self.matching_blocks[i]
                if prev_b + prev_len == cur_b or prev_a + prev_len == cur_a:
                    prev_slice_a = self.a[cur_a - prev_len:cur_a]
                    prev_slice_b = self.b[cur_b - prev_len:cur_b]
                    if prev_slice_a == prev_slice_b:
                        cur_b -= prev_len
                        cur_a -= prev_len
                        cur_len += prev_len
                        i -= 1
                        continue
                break
            mb.append((cur_a, cur_b, cur_len))
        mb.reverse()
        self.matching_blocks = mb

    def build_matching_blocks(self, last_snake):
        """Build list of matching blocks based on snakes

        The resulting blocks take into consideration multiple preprocessing
        optimizations:
         * add separate blocks for common prefix and suffix
         * shift positions and split blocks based on the list of discarded
           non-matching lines
        """
        self.matching_blocks = matching_blocks = []

        common_prefix = self.common_prefix
        common_suffix = self.common_suffix
        a_index = self.a_index
        b_index = self.b_index
        while last_snake is not None:
            last_snake, x, y, snake = last_snake
            if self.lines_discarded:
                # split snakes if needed because of discarded lines
                x += snake - 1
                y += snake - 1
                x_prev = a_index[x] + common_prefix
                y_prev = b_index[y] + common_prefix
                if snake > 1:
                    new_snake = 1
                    for i in range(1, snake):
                        x -= 1
                        y -= 1
                        x_next = a_index[x] + common_prefix
                        y_next = b_index[y] + common_prefix
                        if (x_prev - x_next != 1) or (y_prev - y_next != 1):
                            matching_blocks.insert(0, (x_prev, y_prev, new_snake))
                            new_snake = 0
                        x_prev = x_next
                        y_prev = y_next
                        new_snake += 1
                    matching_blocks.insert(0, (x_prev, y_prev, new_snake))
                else:
                    matching_blocks.insert(0, (x_prev, y_prev, snake))
            else:
                matching_blocks.insert(0, (x + common_prefix,
                                           y + common_prefix, snake))
        if common_prefix:
            matching_blocks.insert(0, (0, 0, common_prefix))
        if common_suffix:
            matching_blocks.append((
                len(self.a) - common_suffix,
                len(self.b) - common_suffix,
                common_suffix
            ))
        matching_blocks.append((len(self.a), len(self.b), 0))
        # clean-up to free memory
        self.a_index = self.b_index = None

    def initialise(self):
        """
        Optimized implementation of the O(NP) algorithm described by Sun Wu,
        Udi Manber, Gene Myers, Webb Miller
        ("An O(NP) Sequence Comparison Algorithm", 1989)
        http://research.janelia.org/myers/Papers/np_diff.pdf
        """
        a, b = self.preprocess()
        m = len(a)
        n = len(b)
        middle = m + 1
        last_snake = None
        delta = n - m + middle
        d_min = min(middle, delta)
        d_max = max(middle, delta)
        if n > 0 and m > 0:
            size = n + m + 2
            fp = [(-1, None)] * size
            p = -1
            while True:
                p += 1
                if not p % 100:
                    yield None
                # move along vertical edge
                yv = -1
                node = None
                for km in range(d_min - p, delta, 1):
                    t = fp[km + 1]
                    if yv < t[0]:
                        yv, node = t
                    else:
                        yv += 1
                    x = yv - km + middle
                    if x < m and yv < n and a[x] == b[yv]:
                        snake = x
                        x += 1
                        yv += 1
                        while x < m and yv < n and a[x] == b[yv]:
                            x += 1
                            yv += 1
                        snake = x - snake
                        node = (node, x - snake, yv - snake, snake)
                    fp[km] = (yv, node)
                # move along horizontal edge
                yh = -1
                node = None
                for km in range(d_max + p, delta, -1):
                    t = fp[km - 1]
                    if yh <= t[0]:
                        yh, node = t
                        yh += 1
                    x = yh - km + middle
                    if x < m and yh < n and a[x] == b[yh]:
                        snake = x
                        x += 1
                        yh += 1
                        while x < m and yh < n and a[x] == b[yh]:
                            x += 1
                            yh += 1
                        snake = x - snake
                        node = (node, x - snake, yh - snake, snake)
                    fp[km] = (yh, node)
                # point on the diagonal that leads to the sink
                if yv < yh:
                    y, node = fp[delta + 1]
                else:
                    y, node = fp[delta - 1]
                    y += 1
                x = y - delta + middle
                if x < m and y < n and a[x] == b[y]:
                    snake = x
                    x += 1
                    y += 1
                    while x < m and y < n and a[x] == b[y]:
                        x += 1
                        y += 1
                    snake = x - snake
                    node = (node, x - snake, y - snake, snake)
                fp[delta] = (y, node)
                if y >= n:
                    last_snake = node
                    break
        self.build_matching_blocks(last_snake)
        self.postprocess()
        yield 1
