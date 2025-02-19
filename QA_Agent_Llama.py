import streamlit as st
import pandas as pd
import simplejson as json
import re
from autogen import UserProxyAgent, AssistantAgent

# Streamlit UI Setup
st.set_page_config(page_title="QA Test Case Generator", layout="wide")
st.markdown("<h1 style='text-align: center; font-size: 32px;'>🧪 AI-Powered QA Test Case Generator</h1>", unsafe_allow_html=True)

# Sample User Stories for Copy-Paste
sample_stories = """ 
User Login => As a user, I want to log in so that I can access my account.

Password Reset => As a user, I want to reset my password so that I can regain access to my account if I forget my credentials.

Product Checkout => As a customer, I want to add products to my cart and proceed to checkout so that I can purchase items online.

Profile Update => As a user, I want to update my profile information so that I can keep my account details up to date.

Search Functionality => As a user, I want to search for products by name or category so that I can quickly find what I need.
"""

st.markdown("### 📜 Sample User Stories (Copy-Paste)")
st.code(sample_stories, language="text")
st.write("Enter a user story, and the AI will generate detailed test cases for you!")

# User Input
user_story = st.text_area("📜 Enter User Story:", "As a user, I want to log in so that I can access my account.")

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


# Generate Button
if st.button("🚀 Generate Test Cases"):
    with st.spinner("Generating test cases..."):
        test_cases = generate_test_cases(user_story)

        if test_cases:
            # Convert JSON data into a DataFrame
            df = pd.DataFrame(test_cases)
            st.dataframe(df)

            # Download as CSV
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Test Cases as CSV", data=csv, file_name="test_cases.csv", mime="text/csv")
        else:
            st.error("❌ Failed to generate test cases. Check AI response.")
