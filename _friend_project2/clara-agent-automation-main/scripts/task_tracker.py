import csv
import os

def create_task(account_id, stage, output_dir):

    task_file = os.path.join(output_dir, "task_tracker.csv")

    row = [account_id, stage]

    exists = os.path.exists(task_file)

    with open(task_file, "a", newline="") as f:
        writer = csv.writer(f)

        if not exists:
            writer.writerow(["account_id","stage"])

        writer.writerow(row)