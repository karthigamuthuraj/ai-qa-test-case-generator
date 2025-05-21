from flask import Flask, render_template, request, make_response
import pandas as pd
import simplejson as json
import re
from autogen import UserProxyAgent, AssistantAgent

app = Flask(__name__)

last_generated_test_cases = None

config_list = [
    {
        "model": "llama3.2",
        "api_type": "ollama",
        "stream": False,
    }
]

# AutoGen Agents Setup
qa_agent = AssistantAgent(
    name="QA_Agent",
    max_consecutive_auto_reply=1,
    human_input_mode="NEVER",
    llm_config={
        "timeout": 600,
        "cache_seed": 42,
        "config_list": config_list,
    }
)

user_proxy = UserProxyAgent(
    name="User",
    max_consecutive_auto_reply=1,
    human_input_mode="NEVER",
    code_execution_config=False
)

# Function to Generate Test Cases
def generate_test_cases(story):
    prompt = f"""
    Generate **detailed** test cases for the following user story:
    {story}

    Include:
    - Functional test cases
    - Regression test cases
    - Integration test cases
    - Performance test cases
    - Security test cases
    - Positive test cases
    - Edge test cases
    - Negative test cases

    Each test case should include all the following fields in a JSON format: 
    - ID: Unique test case ID
    - Summary: A brief description of the test objective.
    - Test Type: Functional, Regression, Integration, Performance, Security, etc.
    - Priority: High, Medium, or Low based on impact.
    - Component: The feature or module under test.
    - Step Description: Actions to be performed.
    - Expected Result: The expected system behavior after executing the step.
    - Actual Result: (To be recorded during test execution).
    - Pass/Fail Status: (To be marked after execution).
    
    **Return the test case Output Requirements:**
    - Return only a **valid JSON object**.
    - Do **not** include markdown (` ```json `), explanations, or extra text.
    - Do **not** include extra characters, escape sequences, explanations, or markdown.
    - The response **must be valid JSON** without escape sequences (`\`).

    Example format:
    [
        {{"ID": "TC001", "Summary": "Verify login with valid credentials", "Test Type": "Functional", "Priority": "High", "Component": "Login", "Step Description": "Enter valid username and password, then click login", "Expected Result": "User should be logged in", "Actual Result": "", "Pass/Fail Status": ""}}
    ]
    """
    
    # Initiating chat with the QA agent
    response = user_proxy.initiate_chat(qa_agent, message=prompt)

    # Extract JSON from AI response
    return extract_json_from_response(response)

# Function to Extract JSON from AI Response
def extract_json_from_response(response):
    raw_response = str(response.chat_history)
    raw_response = raw_response.replace("\\n", "\n")
   
    # Find all JSON code blocks inside triple backticks
    matches = re.findall(r'```(?:json)?\n(.*?)\n```', raw_response, re.DOTALL)
    
    for match in matches:
        match = match.strip()  # Normalize the JSON format
        
        # Clean up any unnecessary whitespace or newlines within the JSON string
        cleaned_json = match.replace("\n", "").replace("\t", "")
        cleaned_json = cleaned_json.replace("\\", "\\\\")  # Escape backslashes properly
        
        try:
            parsed_json = json.loads(cleaned_json)
           
            return parsed_json  # Return the first valid JSON found
        except json.JSONDecodeError:
            print("❌ Failed to parse JSON:", cleaned_json)  # Print the failed block for debugging
            continue  # Skip and try the next match
    
    print("❌ Failed to parse AI response as JSON.")
    return None

@app.route('/', methods=['GET', 'POST'])
def home():
    test_cases = None
    error_message = None
    user_story_text = ''
    global last_generated_test_cases

    if request.method == 'POST':
        user_story_text = request.form.get('user_story', '')
        if user_story_text:
            try:
                test_cases_json = generate_test_cases(user_story_text)
                if test_cases_json:
                    test_cases = test_cases_json
                    last_generated_test_cases = test_cases  # Store for download
                else:
                    error_message = "Failed to generate test cases. The AI response might be invalid or empty."
                    last_generated_test_cases = None
            except Exception as e:
                print(f"Error during test case generation: {e}") # For debugging
                error_message = "An unexpected error occurred while generating test cases."
                last_generated_test_cases = None
        else:
            error_message = "User story cannot be empty."
            last_generated_test_cases = None
    
    # If it's a GET request and there are no test cases being generated,
    # ensure last_generated_test_cases is None if we are not displaying anything from a previous POST.
    # This logic might need refinement based on desired behavior for GET requests clearing previous results.
    # For now, we only explicitly clear it on POST failures or empty inputs.

    return render_template('index.html', test_cases=test_cases, error_message=error_message, user_story_text=user_story_text)

@app.route('/download_csv')
def download_csv():
    global last_generated_test_cases
    if last_generated_test_cases:
        try:
            df = pd.DataFrame(last_generated_test_cases)
            csv_data = df.to_csv(index=False)
            
            response = make_response(csv_data)
            response.headers["Content-Disposition"] = "attachment; filename=test_cases.csv"
            response.headers["Content-Type"] = "text/csv"
            return response
        except Exception as e:
            print(f"Error during CSV generation: {e}") # For debugging
            # Potentially pass an error message to the template or redirect
            return "Error generating CSV. Please try again.", 500
    else:
        # Potentially redirect to home with an error message
        return "No test cases available to download. Please generate some first.", 404

if __name__ == '__main__':
    app.run(debug=True)
