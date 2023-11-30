import os
import time  # Import the time module
from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import csv
from dotenv import load_dotenv
import json

# IBM Cloud and Watson Assistant credentials
load_dotenv()
api_key = os.getenv("assistant_api_key", None)
service_url = os.getenv("assistant_service_url", None)
assistant_id = os.getenv("assistant_environment_id_RJ_ESG_assistant", None)

# Initialize the Watson Assistant client
authenticator = IAMAuthenticator(api_key)
assistant = AssistantV2(
    version='2023-06-15',
    authenticator=authenticator
)
assistant.set_service_url(service_url)

# Create a session
session = assistant.create_session(assistant_id=assistant_id).get_result()
session_id = session['session_id']

# Define the input files
questions_file = 'questions.txt'
companies_file = 'companies.txt'

# Read the list of companies from companies.txt
with open(companies_file, 'r') as companies_file:
    companies = [line.strip() for line in companies_file if line.strip()]

# Read questions from the input file and generate answers for each company
with open(questions_file, 'r') as questions_file:
    for question_template in questions_file:
        question_template = question_template.strip()
        question_words = question_template.split()
        if question_template:
            # Determine the output file name
            output_file = f"{question_words[1]}_areas.csv" if question_words[1] in ["cause", "impact"] else f"{question_words[1]}.csv"

            with open(output_file, 'w', newline='') as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(['Company', 'Question', 'Response'])  # Write the header

                for company in companies:
                    success = False
                    attempts = 0
                    max_attempts = 3  # Maximum number of attempts per company
                    while not success and attempts < max_attempts:
                        try:
                            print(f"processing {company} for question: {question_template}")
                            question = question_template.replace('%s', company)
                            response = assistant.message(
                                assistant_id=assistant_id,
                                session_id=session_id,
                                input={
                                    'message_type': 'text',
                                    'text': question
                                },
                            ).get_result()
                            response_text = response['output']['generic'][0]['text']
                            csv_writer.writerow([company, question, response_text])  # Write to CSV
                            success = True
                        except KeyError:
                            attempts += 1
                            print(f"KeyError encountered for {company}. Attempt {attempts} of {max_attempts}. Retrying...")
                            time.sleep(5)  # Delay for 5 seconds before retrying

            print(f'Answers for "{question_template}" saved to {output_file}\n')

# Delete the session when done
assistant.delete_session(assistant_id=assistant_id, session_id=session_id)
