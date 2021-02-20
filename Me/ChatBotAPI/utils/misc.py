import collections
from typing import List




def modify_nested_dict(d, func):
    for k, v in d.items():
        if(isinstance(v, collections.Mapping)):
            modify_nested_dict(v, func)
        elif(isinstance(v, List)):
            if(isinstance(v[0], collections.Mapping)):
                d[k] = [modify_nested_dict(i, func) for i in v]
            else:
                d[k] = [func(i) for i in v]
        else:
            d[k] = func(v)
    return d