from .myers import DiffChunk, MyersSequenceMatcher


class SyncPointMyersSequenceMatcher(MyersSequenceMatcher):

    def __init__(self, isjunk=None, a="", b="", syncpoints=None):
        super().__init__(isjunk, a, b)
        self.isjunk = isjunk
        self.sync_points = syncpoints

    def initialise(self):
        if self.sync_points is None or len(self.sync_points) == 0:
            for i in MyersSequenceMatcher.initialise(self):
                yield i
        else:
            chunks = []
            ai = 0
            bi = 0
            for aj, bj in self.sync_points:
                chunks.append((ai, bi, self.a[ai:aj], self.b[bi:bj]))
                ai = aj
                bi = bj
            if ai < len(self.a) or bi < len(self.b):
                chunks.append((ai, bi, self.a[ai:], self.b[bi:]))

            self.split_matching_blocks = []
            self.matching_blocks = []
            for ai, bi, a, b in chunks:
                matching_blocks = []
                matcher = MyersSequenceMatcher(self.isjunk, a, b)
                for i in matcher.initialise():
                    yield None
                blocks = matcher.get_matching_blocks()
                l = len(matching_blocks) - 1
                if l >= 0 and len(blocks) > 1:
                    aj = matching_blocks[l][0]
                    bj = matching_blocks[l][1]
                    bl = matching_blocks[l][2]
                    if (aj + bl == ai and bj + bl == bi and
                        blocks[0][0] == 0 and blocks[0][1] == 0):
                        block = blocks.pop(0)
                        matching_blocks[l] = (aj, bj, bl + block[2])
                for x, y, l in blocks[:-1]:
                    matching_blocks.append((ai + x, bi + y, l))
                self.matching_blocks.extend(matching_blocks)
                # Split matching blocks each need to be terminated to get our
                # split chunks correctly created
                self.split_matching_blocks.append(
                    matching_blocks + [(ai + len(a), bi + len(b), 0)])
            self.matching_blocks.append((len(self.a), len(self.b), 0))
            yield 1

    def get_opcodes(self):
        # This is just difflib.SequenceMatcher.get_opcodes in which we instead
        # iterate over our internal set of split matching blocks.
        if self.opcodes is not None:
            return self.opcodes
        i = j = 0
        self.opcodes = opcodes = []
        self.get_matching_blocks()
        for matching_blocks in self.split_matching_blocks:
            for ai, bj, size in matching_blocks:
                tag = ''
                if i < ai and j < bj:
                    tag = 'replace'
                elif i < ai:
                    tag = 'delete'
                elif j < bj:
                    tag = 'insert'
                if tag:
                    opcodes.append((tag, i, ai, j, bj))
                i, j = ai + size, bj + size
                # the list of matching blocks is terminated by a
                # sentinel with size 0
                if size:
                    opcodes.append(('equal', ai, i, bj, j))
        return [DiffChunk._make(chunk) for chunk in opcodes]
