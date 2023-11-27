import os
import csv
import re

# Predefined order of companies
company_order = [
    "Novartis", "J&J", "Pfizer", "WellsFargo", "Ford", "Honda", "GeneralMotors", "Toyota",
    "Verizon", "Netflix", "Apple", "Microsoft", "Amazon", "Facebook", "Alphabet", "KDP",
    "Coke", "Oracle", "Nvidia", "Micron", "AMD", "Qualcomm"
]

def extract_section_and_explanation(content, section_start, next_section_start):
    # Regular expression to match the section and its explanation
    section_regex = rf"{section_start}(.*?)(?=\n{next_section_start}|\Z)"
    match = re.search(section_regex, content, re.DOTALL)
    if match:
        section_content = match.group(1).strip()
        # Split the content into list and explanation parts
        list_part, _, explanation_part = section_content.partition("\nExplanation:")
        return list_part.strip(), explanation_part.strip()
    return '', ''

def process_file(file_path, company_name, all_data):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Extracting different sections and their explanations
    cause_areas, cause_explanation = extract_section_and_explanation(
        content,
        f"Cause areas {company_name} focuses on:",
        "Demographics " + company_name + " focuses on:"
    )
    demographics, demo_explanation = extract_section_and_explanation(
        content,
        f"Demographics {company_name} focuses on:",
        "Impact Areas " + company_name + " focuses on:"
    )
    impact_areas, impact_explanation = extract_section_and_explanation(
        content,
        f"Impact Areas {company_name} focuses on:",
        "End of Document"  # Placeholder for end of document
    )

    # Aggregating data
    all_data['cause_areas'][company_name] = (cause_areas, cause_explanation)
    all_data['demographics'][company_name] = (demographics, demo_explanation)
    all_data['impact_areas'][company_name] = (impact_areas, impact_explanation)

def write_to_csv(data, file_name):
    with open(file_name, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Company Name', 'List of Items', 'Explanation'])
        for company in company_order:  # Sorting data based on predefined order
            if company in data:
                items, explanation = data[company]
                writer.writerow([company, items, explanation])

directory_path = '/Users/pvsh/PycharmProjects/wx-demos-release/esg-assistant/data/10K-inferences'  # Replace with the path to your directory
all_data = {'cause_areas': {}, 'demographics': {}, 'impact_areas': {}}

for filename in os.listdir(directory_path):
    if filename.endswith('.txt'):  # Assuming the files are text files
        file_path = os.path.join(directory_path, filename)
        company_name = os.path.basename(file_path).split('-')[0]
        process_file(file_path, company_name, all_data)

# Writing to CSV files
write_to_csv(all_data['cause_areas'], 'all_cause_areas.csv')
write_to_csv(all_data['demographics'], 'all_demographics.csv')
write_to_csv(all_data['impact_areas'], 'all_impact_areas.csv')
