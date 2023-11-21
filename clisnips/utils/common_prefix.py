def common_prefix(*args: str) -> str:
    s1 = min(args)
    s2 = max(args)
    common = s1
    for i, char in enumerate(s1):
        if char != s2[i]:
            common = s1[:i]
            break
    return common
