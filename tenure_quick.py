
import csv

def quick():
    in_file = open("cscw_output_label_tenure.csv", "r")
    csv_in = csv.reader(in_file)
    found = False
    print("Checking")

    mapping = {}
    for line in csv_in:
        if len(line) > 0 and "Keyed Comments" in line[0]:
            found = False

        if found and len(line) > 0:
            key = line[0]
            label = key.split(" ")[0]
            if label not in mapping.keys():
                mapping[label] = {}

            tenure = int(key.split(" ")[1])
            count = int(line[1])
            succ = float(line[2])
            inf = float(line[3])

            if tenure not in mapping[label].keys():
                mapping[label][tenure] = {
                    "Count":count,
                    "Success":succ,
                    "Impact":inf
                }
        if len(line) > 0 and "Keyed Votes" in line[0]:
            found = True

    total = 0
    at_least_n = {}

    for k in mapping.keys():
        for ten in mapping[k].keys():
            print(ten)
            total += mapping[k][ten]["Count"]
    
    cume = 0
    cume_succ = 0.0
    cume_imp = 0.0
    for i in range(100):
        for k in ["Delete"]:
            cume += mapping[k][i]["Count"]
            cume_succ += mapping[k][i]["Count"]*mapping[k][i]["Success"]
            cume_imp += mapping[k][i]["Count"]*mapping[k][i]["Impact"]
        print("First {} posts: {}, {}, {}".format(i, (cume/total), (cume_succ/cume), (cume_imp/cume)))

    if False:
        out_file = open("tenure_collapse.csv", "w")
        csv_write = csv.writer(out_file)

        header = ["Tenure","Keep Imp","Keep Succ","Keep Count","Delete Imp","Delete Succ", "Delete Count"]
        csv_write.writerow(header)
        for tenure in range(1,1000):
            dels = mapping["Delete"][tenure]
            keeps = mapping["Keep"][tenure]
            row = [tenure, keeps["Impact"], keeps["Success"], keeps["Count"], dels["Impact"], dels["Success"], dels["Count"]]
            csv_write.writerow(row)

if __name__ == "__main__":
    quick()