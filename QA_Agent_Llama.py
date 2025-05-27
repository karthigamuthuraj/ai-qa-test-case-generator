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
    chat_messages = response.chat_history

    # Look for the user response from the AI agent (role == 'user' or 'assistant')
    for message in reversed(chat_messages):
        if 'content' in message and isinstance(message['content'], str):
            possible_json = message['content'].strip()

            # Try parsing directly
            try:
                return json.loads(possible_json)
            except json.JSONDecodeError:
                pass  # fallback to regex below

            # Try regex fallback if direct load fails
            match = re.search(r'(\[\s*{.*?}\s*\])', possible_json, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError as e:
                    print("❌ JSON decode failed:", e)
                    print("🔧 Problematic JSON Block:\n", match.group(1))
                    return None

    print("❌ No valid JSON found in chat history.")
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
