import os
import json

def get_flats():
    caches = os.listdir("cache/bert")
    for c in caches:
        if "json" in c:
            continue
        cachepath = os.path.join("cache","bert",c)
        cache_in = open(cachepath,"r").read().split()
        vals = []
        if(len(cache_in) > 0):
            cache_in[-1] = cache_in[-1].replace("]]","")
            if(cache_in[0] == "[["):
                cache_in = cache_in[1:]
            while(cache_in[0].startswith("[")):
                cache_in[0] = cache_in[0].replace("[","")
            for i in cache_in:
                vals.append(float(i))  
            json_path = os.path.join("cache","bert",c)
            file_out = open(json_path, "w")
        print(json.dumps(vals), file=file_out)

def consolidate_caches():
    cachepath = os.path.join("..","cache","bert_clean")
    if (os.path.exists(cachepath)):
        categories = os.listdir(cachepath)
        for cat in categories:
            print(cat)
            if not os.path.isfile(cat):
                catpath = os.path.join(cachepath, cat)
                if os.path.exists(catpath):
                    subcat = os.listdir(catpath)
                    for sub in subcat:
                        if not os.path.isfile(sub):
                            subcatpath = os.path.join(catpath, sub)
                            print("    {}".format(subcatpath))
                            caches = os.listdir(subcatpath)
                            subdir_text = []
                            for cache_id in caches:
                                individual_path = os.path.join(subcatpath, cache_id)
                                cache_in = open(individual_path, "r").read()
                                subdir_text.extend([cache_id, cache_in])
                            cache_out_path = os.path.join(catpath, "{}.txt".format(sub))
                            cache_out = open(cache_out_path, "w")
                            for t in subdir_text:
                                print(t, file=cache_out)

if __name__ == "__main__":
    consolidate_caches()