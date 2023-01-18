import csv


def pretty_table(lst, col_sep=2):
    """
    Print a list of dictionary in a table format
    :param lst: the dictionary list to print
    :param col_sep: the distance between 2 columns
    """
    if not lst:
        return

    # Find the max length of each key
    maxvalueslen_by_keys = {}
    for key in lst[0].keys():
        maxvaluelen = max(len(elem[key]) for elem in lst)
        maxvalueslen_by_keys[key] = maxvaluelen+col_sep

    for i in range(len(lst)):
        print_str = ""

        # Header
        if i == 0:
            for k, v in lst[i].items():
                print_str += f"{k: <{maxvalueslen_by_keys[k]}}"
            print(print_str)
            print_str = ""

        # Body
        for k, v in lst[i].items():
            print_str += f"{v: <{maxvalueslen_by_keys[k]}}"
        print(print_str)


def save_csv(lst, path):
    if not lst:
        return

    csv_columns = list(lst[0].keys())
    try:
        with open(path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            for elem in lst:
                writer.writerow(elem)
    except IOError:
        print("I/O error")


def load_csv(path):
    try:
        with open(path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            ports = [row for row in reader]
    except IOError:
        print("I/O error")

    return ports