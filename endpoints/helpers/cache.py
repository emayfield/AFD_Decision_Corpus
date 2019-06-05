import os

def lookup(cache_path, function_key, key):
#    print("LOOKUP {}".format(key))
    for f in function_key:
        code_subdir = str(key)[0:1]
        cache_subdir = str(key)[1:5]
        cache_file = os.path.join(cache_path, f, code_subdir, cache_subdir, str(key))
        cache_dir = os.path.dirname(cache_file)
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        cache_exists = os.path.isfile(cache_file)
        if cache_exists:
            try:
                file_in = open(cache_file, "r").read()
    #            print("SUCCESS {}".format(key))
                return 200, file_in
            except:
                continue
    return 500, None


def old_lookup(cache_path, function_key, key):
#    print("LOOKUP {}".format(key))
    for f in function_key:
        code_subdir = str(key)[0:1]
        cache_subdir = str(key)[1:5]
        cache_file = os.path.join(cache_path, f, code_subdir, cache_subdir, str(key))
        cache_dir = os.path.dirname(cache_file)
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        cache_exists = os.path.isfile(cache_file)
        if cache_exists:
            try:
                file_in = open(cache_file, "r").read()
    #            print("SUCCESS {}".format(key))
                return 200, file_in
            except:
                continue
    return 500, None

def store(cache_path, function_key, key, val):
    code_subdir = str(key)[0:1]
    cache_subdir = str(key)[1:5]
    dir = os.path.join(cache_path, function_key[0], code_subdir, cache_subdir)
    if not os.path.exists(dir):
        os.makedirs(dir)
    cache_file = os.path.join(cache_path, function_key[0], code_subdir, cache_subdir, str(key))
    file_out = open(cache_file, "w")
#    print("STORED KEY {} {}".format(str(key), val))
    print(val, file=file_out)
    return 201, cache_file