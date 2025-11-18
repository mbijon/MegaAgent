import pandas as pd
import os
import shutil
import subprocess

# File paths
val_file_path = 'travel_planner_val.xlsx'
config_file_path = 'config.py'
main_script_path = 'main.py'
output_folder = './'
plan_folder = 'files/plan.json'

# Load the Excel file
val_data = pd.read_excel(val_file_path)

# Read config.py file
with open(config_file_path, 'r', encoding='utf-8') as file:
    config_content = file.read()

# Function to update additional_prompt
def update_additional_prompt(config_content, row):
    query = row['query']
    ref_info = row['reference_information']
    new_prompt = '''
Your company's current goal is to develop a travel plan in 'plan.json', in the format:

{{"plan":[{{"day": 1, "current_city": "from [City A] to [City B]", "transportation": "Flight Number: XXX, from A to B", "breakfast": "-", "attraction": "Name, City;Name, City;...;Name, City;", "lunch": "Name, City", "dinner": "Name, City", "accommodation": "Name, City"}}, {{"day": 2, "current_city": "City B", "transportation": "-", "breakfast": "Name, City", "attraction": "Name, City;Name, City;", "lunch": "Name, City", "dinner": "Name, City", "accommodation": "Name, City"}}, ...]}}
where "-" denotes not applicable(like the accommodation of the last day, or the meal on the plane/car).
'''+f'''
Here are the customers' requirements:
{query} You cannot choose the same restaurant for two different meals.

Here are all the needed information. You cannot query more. Be careful with room rules and Minimum Nights Stay!
{ref_info}

You MUST use exactly <talk goal="Name">TalkContent</talk> format to talk to others, like:

<talk goal="Alice">Alice, I have completed 'a.txt'. Please check it for your work and talk to me again if needed. </talk>. 

Otherwise, they will not receive your message, and the conversation will terminate. "Name" should only be ONE specific employee. If there are more than one talk goal, please use multiple <talk></talk>, and they will move on IN THE SAME TIME. 

You must use function calls in JSON for file operations.

Leave a remarkable TODO wherever there is an unfinished task. Please keep updating your TODO list until everything is done. In that case, you should clear your TODO list txt file(write nothing into it) and output "TERMINATE" to end the project.
'''
    updated_content = config_content.replace(
        config_content[config_content.find("additional_prompt = r'''") + len("additional_prompt = r'''"):config_content.find("'''", config_content.find("additional_prompt = r'''") + len("additional_prompt = r'''"))],
        new_prompt
    )
    return updated_content

# Iterate through each row
for index, row in val_data.iterrows():
    # Update config.py file
    updated_config_content = update_additional_prompt(config_content, row)

    # Temporarily save the updated config.py
    temp_config_path = f'config.py'
    with open(temp_config_path, 'w', encoding='utf-8') as file:
        file.write(updated_config_content)

    # Run main.py
    try:
        subprocess.run(["python", main_script_path], check=True)

        # Copy the generated plan.json to the target file
        if os.path.exists(plan_folder):
            output_plan_path = os.path.join(output_folder, f'plan{index}.json')
            shutil.copy(plan_folder, output_plan_path)
            print(f"Plan for row {index} saved as {output_plan_path}.")
        else:
            print(f"Plan for row {index} not found. Ensure main.py created the file.")
    except subprocess.CalledProcessError as e:
        print(f"Error running main.py for row {index}: {e}")
    except FileNotFoundError:
        print(f"File not found during processing of row {index}. Ensure paths are correct.")
    