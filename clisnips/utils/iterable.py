

def join(delimiter, iterable):
    it = iter(iterable)
    yield next(it)
    for x in it:
        yield delimiter
        yield x
