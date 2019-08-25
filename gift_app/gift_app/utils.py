from functools import reduce


missing = object()


def merge_dicts(*dicts):
    def merge(a: dict, b: dict) -> dict:
        m = {}
        for key in a.keys() | b.keys():
            a_val = a.get(key, missing)
            b_val = b.get(key, missing)
            # Хотя бы одно из них должно присутствовать.
            assert not (a_val is missing and b_val is missing)
            if isinstance(b_val, dict) or isinstance(a_val, dict):
                if b_val is missing:
                    b_val = {}
                if a_val is missing:
                    a_val = {}
                m[key] = merge(a_val, b_val)
                continue
            m[key] = b_val if b_val is not missing else a_val
        return m

    d = reduce(merge, dicts, {})
    return d
