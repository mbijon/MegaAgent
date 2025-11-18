import json
import pandas as pd
from pathlib import Path
import chardet

def detect_encoding(file_path):
    """Detect the encoding for a plan file."""
    with open(file_path, 'rb') as f:
        raw_data = f.read()
    result = chardet.detect(raw_data)
    return result['encoding']

def read_plan_file(file_path):
    """Read one plan JSON file while handling encoding issues automatically."""
    try:
        # Try UTF-8 first
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)['plan']
    except UnicodeDecodeError:
        # If UTF-8 fails, detect the encoding and retry
        encoding = detect_encoding(file_path)
        print(f"Detected encoding for {file_path}: {encoding}")

        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return json.load(f)['plan']
        except Exception as e:
            # Fall back to other common encodings
            for enc in ['gbk', 'gb2312', 'gb18030', 'latin1', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        return json.load(f)['plan']
                except Exception:
                    continue
            # Give up if every attempt fails
            raise e

def merge_travel_plans():
    """Merge every travel plan and attach the original query."""
    # Read queries from the spreadsheet
    try:
        df = pd.read_excel('travel_planner_val.xlsx')
    except Exception as e:
        print(f"Error reading Excel file: {str(e)}")
        return

    # Track failures for post-run inspection
    error_files = []
    success_count = 0

    # Stream directly to disk, one plan per line
    with open('merged_plans.jsonl', 'w', encoding='utf-8') as outfile:
        # Iterate through every possible plan file (plan0.json ... plan179.json)
        for idx in range(180):
            plan_file = f'plan{idx}.json'

            # Skip missing files
            if not Path(plan_file).exists():
                print(f"Warning: {plan_file} not found, skipping...")
                continue

            try:
                # Read the plan file
                plan_data = read_plan_file(plan_file)

                # Load the matching query if available
                if idx < len(df):
                    query = df.iloc[idx]['query']
                else:
                    print(f"Warning: No query found for index {idx}")
                    query = ""

                # Build the JSON line entry
                plan_entry = {
                    "idx": idx,
                    "query": query,
                    "plan": plan_data
                }

                # Persist the plan without indentation to keep one entry per line
                json_line = json.dumps(plan_entry, ensure_ascii=False)
                outfile.write(json_line + '\n')

                success_count += 1
                print(f"Successfully processed {plan_file}")

            except Exception as e:
                error_msg = f"Error processing {plan_file}: {str(e)}"
                print(error_msg)
                error_files.append({"file": plan_file, "error": str(e)})

    # Print a summary for the operator
    print(f"\nSummary:")
    print(f"Successfully processed {success_count} plans into merged_plans.jsonl")

    if error_files:
        print("\nFiles with errors:")
        for error in error_files:
            print(f"- {error['file']}: {error['error']}")

if __name__ == "__main__":
    merge_travel_plans()