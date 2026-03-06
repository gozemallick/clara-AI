def generate_changelog(changes, path):

    with open(path, "w", encoding="utf-8") as f:

        f.write("CHANGELOG (v1 -> v2)\n\n")

        if not changes:
            f.write("No changes detected\n")
        else:
            for change in changes:
                f.write(f"- {change}\n")