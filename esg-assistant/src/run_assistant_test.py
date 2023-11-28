import os
from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import csv
from dotenv import load_dotenv

# IBM Cloud and Watson Assistant credentials: Discover Simple
load_dotenv()
api_key = os.getenv("assistant_api_key", None)
service_url = os.getenv("assistant_service_url", None)
assistant_id = os.getenv("assistant_environment_id_RJ_ESG_assistant", None)

# Initialize the Watson Assistant client
authenticator = IAMAuthenticator(api_key)
assistant = AssistantV2(
    version='2023-06-15',  # Use the appropriate API version
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
        if question_template:
            # Create a new CSV file for each question
            output_file = f'qa_output_{question_template.replace(" ", "_")}.csv'
            with open(output_file, 'w', newline='') as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(['Company', 'Question', 'Response'])  # Write the header

                for company in companies:
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
                    print(response)
                    response_text = response['output']['generic'][0]['text']
                    csv_writer.writerow([company, question, response_text])  # Write company, question, and answer to CSV

            print(f'Answers for "{question_template}" saved to {output_file}')

# Delete the session when done
assistant.delete_session(assistant_id=assistant_id, session_id=session_id)
