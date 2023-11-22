import os
import re
import datetime
import json
from dotenv import load_dotenv

from run_discovery import WatsonDiscovery
from run_watsonx_ai import WatsonxAI

from ibm_watson_machine_learning.foundation_models.utils.enums import ModelTypes
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams
from ibm_watson_machine_learning.foundation_models.utils.enums import DecodingMethods
from ibm_watson_machine_learning.foundation_models import Model

import pandas as pd

#Global variables
discovery = None
watson_ai = None
companies = None
cause_areas_to_impacts = None
cause_areas_discovery_file = "../data/prompts/cause_areas_discovery_query.txt"
cause_areas_prompt_file = "../data/prompts/cause_areas_mapping.txt"
demographics_prompt_file = "../data/prompts/demographics_mapping.txt"
impact_areas_prompt_file = "../data/prompts/impact_areas_mapping.txt"

ORIGINAL_CAUSE_AREAS = [
    '- Arts and Culture', 
    '- Animal Rights & Welfare', 
    '- Restorative and Criminal Justice',
    '- Disaster Response, Relief, and Recovery',
    '- Diversity, Equity and Inclusion',
    '- Economic Empowerment and Workforce Development',
    '- Education',
    '- Food and Hunger',
    '- Housing and Homelessness',
    '- Sustainability and Environment',
    '- Human Rights', 
    '- Civic Engagement', 
    '- Public Health', 
    '- Science and Technology', 
    '- Poverty Alleviation'
    ]

ORIGINAL_IMPACT_AREAS = [
    '- Increase appreciation and support for the arts',
    '- Reduce criminal activity',
    '- Reduce criminal recidivism',
    '- Achieve financial stability',
    '- Increase access to and acquire employment',
    '- Promote economic growth',
    '- Enhance community infrastructure',
    '- Ensure STEM skills proficiency',
    '- Increase access to quality education programs and services',
    '- Improve academic achievement',
    '- Reduce homelessness',
    '- Increase amount and access to quality affordable housing',
    '- Increase education, awareness and/or understanding of the risks/threat of climate change',
    '- Reduce carbon impact',
    '- Increase land protection and/or conservation',
    '- Increase water protection an/or conservation',
    '- Improve air quality',
    '- Improve water quality',
    '- Reduce hunger and malnutrition',
    '- Increase access to nutritious food',
    '- Increase access to drinkable/potable water',
    '- Increase sustainable food systems',
    '- Increase sustainable water systems',
    '- Achieve equality/eliminate discrimination',
    '- Increase active participation in society',
    '- Increase peace through conflict resolution',
    '- Reduce disease/improve health',
    '- Increase access to quality, affordable healthcare and services',
    '- Improve reproductive health',
    '- Reduce risky and addictive behaviors',
    '- Reduce trauma',
    '- Protect and rescue animals',
    '- Increase access to mental health services',
    '- Advocate for/Promote Policy Change'
    ]

ORIGINAL_DEMOGRAPHICS = [
    '- Seniors and Aging Populations',
    '- Youth/Young People',
    '- Indigenous Peoples',
    '- Immigrants',
    '- Migrants and Refugees',
    '- People who identify as LGTBQ+',
    '- People of Color',
    '- Veterans',
    '- Women and Girls',
    '- People with Disabilities/Differently Abled',
    '- People Experiencing Poverty',
    '- People Experiencing Homelessness',
    '- People Experiencing Obesity and/or Diabetes',
    '- People Experiencing Hunger or Malnourishment',
    '- People Experiencing Mental Illness',
    '- People Experiencing Viruses and Diseases'
    ]

def init():
    global discovery
    global watson_ai
    global companies
    global log_file
    global cause_areas_to_impacts

    load_dotenv()
    #Init discovery invoker
    discovery = WatsonDiscovery(os.getenv("WATSON_DISCOVERY_URL", None), 
                                os.getenv("WATSON_DISCOVERY_API_KEY", None))
    discovery.set_project_name(os.getenv("WATSON_DISCOVERY_PROJECT_NAME", None))
    discovery.set_collection_name(os.getenv("WATSON_DISCOVERY_COLLECTION_NAME", None))

    #Init Watsonx.ai invoker
    watson_ai = WatsonxAI(os.getenv("GENAI_API", None), 
                          os.getenv("GENAI_KEY", None), 
                          os.environ["PROJECT_ID"])
    model_id = ModelTypes.LLAMA_2_70B_CHAT
    parameters = {
        GenParams.DECODING_METHOD: DecodingMethods.GREEDY,
        GenParams.MIN_NEW_TOKENS: 1,
        GenParams.MAX_NEW_TOKENS: 500,
        GenParams.REPETITION_PENALTY: 1.2
    }
    watson_ai.set_model_parameters(model_id, parameters)

    log_file = open(f"./stage1-RAG.log", "w")

    ca_to_impact_map_file="./config/cause_areas_to_impact.json"
    with open(ca_to_impact_map_file) as json_file:
        cause_areas_to_impacts = json.load(json_file)

    # Initialize the list of companies
    # companies = ["coke", "Apple", "Microsoft", "Ford", "Verizon", "WellsFargo", "Netflix", "Amazon"]
    companies = ["coke"]
    #companies = ["coke", "Apple", "Microsoft", "Ford", "Verizon", "Netflix", "Amazon"]
    # companies = ["Nvidia"]
    # companies = ["Pfizer"]
    


def get_prompt(prompt_file):
    with open(prompt_file) as prompt_file:
        theme_prompt = prompt_file.read()
    return theme_prompt

def augment(template_in, context_in ):
    return template_in % ( context_in )

def augment2(template_in, context_1, context_2 ):
    return template_in % ( context_1, context_2 )

def extract_lines(input, start, end):
    extracted_lines = []
    copy = False
    for line in input.splitlines():
        if re.search(start, line) :
            copy = True
            continue
        elif re.search(end, line):
            copy = False
            continue
        elif copy and line != "\n":
            extracted_lines.append(line)

    return extracted_lines

def create_mapping_file(company, cause_areas, cause_areas_explanation, demographics, demographics_explanation, impacts, impacts_explanation):
        inference_file = open(f"../data/10K-inferences/{company}-10K-ESG-Mapping.txt", "w")
        inference_file.write(f"ESG mapping for {company}\n")

        #Dump cause areas
        inference_file.write(f"\nCause areas {company} focuses on:\n")
        for cause_area in cause_areas:
            if cause_area not in ORIGINAL_CAUSE_AREAS:
                continue
            else:
                inference_file.write(f"{cause_area}\n")

        inference_file.write(f"\nExplanation:\n")
        for explanation in cause_areas_explanation:
            inference_file.write(f"\n{explanation}\n")

        #Dump demographics
        inference_file.write(f"\nDemographics {company} focuses on:\n")
        for audience in demographics:
            if audience not in ORIGINAL_DEMOGRAPHICS:
                continue
            else:
                inference_file.write(f"{audience}\n")

        inference_file.write(f"\nExplanation:\n")
        for explanation in demographics_explanation:
            inference_file.write(f"{explanation}\n")

        #Dump impacts
        inference_file.write(f"\nImpact Areas {company} focuses on:\n")
        for impact in impacts:
            if impact not in ORIGINAL_IMPACT_AREAS:
                continue
            else:
                inference_file.write(f"{impact}\n")
                
        inference_file.write(f"\nExplanation:\n")
        for explanation in impacts_explanation:
            inference_file.write(f"{explanation}\n")

        inference_file.close()

def get_mapped_impacts(cause_areas):
    impacts = ""
    # print(cause_areas_to_impacts)
    # available_cause_areas = cause_areas_to_impacts.keys()
    for cause_area in cause_areas:
        if cause_area != '' and cause_areas_to_impacts.get(cause_area) != None:
            mapped_impacts = cause_areas_to_impacts[cause_area]
            for mapped_impact in mapped_impacts:
                impacts += f"{mapped_impact}\n"
    
    return impacts


def main():
    print("Initializing stage1 retrieval process...")
    init()
    log_file.write("Running stage1 retrieval process...")

    #Run stage1 inference for each company
    for company in companies:
        log_file.write(f"Processing the mapping task for: {company}\n")
        print(f"Processing the mapping task for: {company}")
        cause_areas_discovery_query = augment(get_prompt(cause_areas_discovery_file), company)
        log_file.write(f"Discovery query: {cause_areas_discovery_query}")

        query_result = discovery.process_discovery_search(cause_areas_discovery_query, company)
        
        cause_areas = []
        cause_areas_explanation = []
        demographics = []
        demographics_explanation = []
        impacts = []
        impacts_explanation = []

        #print("---DEBUG---")
        #print(query_result['results'])

        # for key, value in query_result.items():
        #     print(key)
        #print(type(query_result['results']), len(query_result['results']))
        #print(type(query_result['results'][0]))
        #print(query_result['results'][0]['document_passages'])
        #print(query_result['results'][0]['extracted_metadata']['filename'])

        #print(query_result['results'][1]['document_passages'])
        #print(query_result['results'][1]['extracted_metadata']['filename'])
        #print(query_result['results']['extracted_metadata']['filename'])


        #print("---END DEBUG---")

        for result in query_result['results']:

            file_name = result['extracted_metadata']['filename']
            log_file.write(f"\nFound relevant passages in source file: {file_name}")

            if(company in file_name):
                log_file.write("\n----------------------------------------------\n")
                print(f"\nMapping cause areas for {company}")
                for passage in result['document_passages']:
                    clean_passage = discovery.format_string(passage['passage_text'])
                    clean_passage += f"\nDocument offset: {passage['start_offset']}"

                    generated_prompt = augment(get_prompt(cause_areas_prompt_file), clean_passage)
                    response = watson_ai.generate(generated_prompt)
                    log_file.write(f"\nCause area prompt:\n{generated_prompt} \nCause area response:\n{response}")

                    cause_areas = cause_areas + extract_lines(response, "Cause Areas", "Explanation")
                    cause_areas_explanation = cause_areas_explanation + extract_lines(response, "Explanation", "go until end")
                    
                    generated_prompt = augment(get_prompt(demographics_prompt_file), clean_passage)
                    response = watson_ai.generate(generated_prompt)
                    log_file.write(f"\nDemographics prompt:\n{generated_prompt} \nDemographics response:\n{response}")

                    demographics = demographics + extract_lines(response, "Demographics", "Explanation")
                    demographics_explanation = demographics_explanation + extract_lines(response, "Explanation", "go until end")

                    mapped_impacts = get_mapped_impacts(cause_areas)
                    generated_prompt = augment2(get_prompt(impact_areas_prompt_file), mapped_impacts, clean_passage)
                    response = watson_ai.generate(generated_prompt)

                    impacts = impacts + extract_lines(response, "Impact Areas", "Explanation")
                    impacts_explanation = impacts_explanation + extract_lines(response, "Explanation", "go until end")
                    log_file.write(f"\nImpact Areas prompt:\n{generated_prompt} \Impact Areas response:\n{response}")

                    log_file.write("\n----------------------------------------------\n")
                
                # Remove duplicates
                cause_areas = list( dict.fromkeys(cause_areas) )
                demographics = list( dict.fromkeys(demographics) )
                impacts = list( dict.fromkeys(impacts) )

                print("<---DEBUG 2---")

                # print("cause areas: ", cause_areas)
                # print(type(cause_areas))
                # print(cause_areas[0], type(cause_areas[0]))
                # cause_areas is a list of strings, but each string has a leading hyphen and space-
                # which need to be removed
                # 
                # cleaned_cause_areas = [item.strip('- ').strip() for item in cause_areas if item] 

                # for cause_area in cause_areas:
                #     if cause_area in ORIGINAL_CAUSE_AREAS:
                #         print("Cause Area: ", cause_area, " : VALID!")
                #     else:
                #         print("Cause Area: ", cause_area, " : NOT IN LIST!")           


                # print("\n<------CAUSE AREAS EXPLANATION: ", cause_areas_explanation)
                # print(cause_areas_explanation[0])
                # print(type(cause_areas_explanation), type(cause_areas_explanation[0]))

                print("<--- END DEBUG---")
                print("<--- END DEBUG---")

                cleaned_cause_areas_explanation = []
                for explanation in cause_areas_explanation:
                    # Check if the starting portion (from '-' to ':') matches any string in the original list
                    if any(explanation.startswith(org) for org in ORIGINAL_CAUSE_AREAS):
                        cleaned_cause_areas_explanation.append(explanation)
                
                '''
                ## MERGE DUPLICATE EXPLANATIONS
                first_portion_dict = {}

                for item in cleaned_cause_areas_explanation:
                    # Find the index of ':' and extract the substring from the beginning to that index
                    first_portion = item.split(':', 1)[0] + ':'
                    
                    # Check if the first portion is already in the dictionary
                    if first_portion not in first_portion_dict:
                        first_portion_dict[first_portion] = item
                    else:
                        # Concatenate the text after the first occurrence
                        first_portion_dict[first_portion] += ' ' + item.split(':', 1)[1]

                # Convert the values of the dictionary back to a list
                result_list = list(first_portion_dict.values())

                print("<<< CAUSE AREAS >>>")
                # Print the result
                for item in result_list:
                    print(item)

                '''

                cleaned_demographics_explanation = []
                for explanation in demographics_explanation:
                    if any(explanation.startswith(org) for org in ORIGINAL_DEMOGRAPHICS):
                        cleaned_demographics_explanation.append(explanation)
                '''
                ## MERGE DUPLICATE EXPLANATIONS
                first_portion_dict = {}

                for item in cleaned_demographics_explanation:
                    # Find the index of ':' and extract the substring from the beginning to that index
                    first_portion = item.split(':', 1)[0] + ':'
                    
                    # Check if the first portion is already in the dictionary
                    if first_portion not in first_portion_dict:
                        first_portion_dict[first_portion] = item
                    else:
                        # Concatenate the text after the first occurrence
                        first_portion_dict[first_portion] += ' ' + item.split(':', 1)[1]

                # Convert the values of the dictionary back to a list
                result_list = list(first_portion_dict.values())

                print("<<<  DEMOGRAPHICS  >>>")
                # Print the result
                for item in result_list:
                    print(item)
                '''


                cleaned_impacts_explanation = []
                for explanation in impacts_explanation:
                    if any(explanation.startswith(org) for org in ORIGINAL_IMPACT_AREAS):
                        cleaned_impacts_explanation.append(explanation)
                '''
                ## MERGE DUPLICATE EXPLANATIONS
                first_portion_dict = {}

                for item in cleaned_impacts_explanation:
                    # Find the index of ':' and extract the substring from the beginning to that index
                    first_portion = item.split(':', 1)[0] + ':'
                    
                    # Check if the first portion is already in the dictionary
                    if first_portion not in first_portion_dict:
                        first_portion_dict[first_portion] = item
                    else:
                        # Concatenate the text after the first occurrence
                        first_portion_dict[first_portion] += ' ' + item.split(':', 1)[1]

                # Convert the values of the dictionary back to a list
                result_list = list(first_portion_dict.values())

                print("<<< IMPACTS >>>")
                # Print the result
                for item in result_list:
                    print(item)
                '''
                
                create_mapping_file(
                    company, 
                    cause_areas, cleaned_cause_areas_explanation,
                    demographics, cleaned_demographics_explanation, 
                    impacts, cleaned_impacts_explanation
                )

    print("Stage 1 mapping inference complete.")
    log_file.close()
                



if __name__ == "__main__":
    main()

    
    

