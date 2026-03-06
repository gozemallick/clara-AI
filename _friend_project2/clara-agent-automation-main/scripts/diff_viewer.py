import json


def compare_dicts(d1, d2, path=""):

    differences = {}

    for key in d1:

        new_path = f"{path}.{key}" if path else key

        if isinstance(d1[key], dict):

            nested = compare_dicts(d1[key], d2.get(key, {}), new_path)

            differences.update(nested)

        else:

            if d1[key] != d2.get(key):

                differences[new_path] = {
                    "v1": d1[key],
                    "v2": d2.get(key)
                }

    return differences


def compare_versions(v1_path, v2_path):

    with open(v1_path, "r", encoding="utf-8") as f:
        v1 = json.load(f)

    with open(v2_path, "r", encoding="utf-8") as f:
        v2 = json.load(f)

    return compare_dicts(v1, v2)


def save_diff(diff_data, output_path):

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(diff_data, f, indent=2)