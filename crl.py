from groq import Groq
import requests
from bs4 import BeautifulSoup
import streamlit as st
import time

# Initialize API key
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]  # Replace with your Groq API key

# Initialize the Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

# Function to fetch and process website content
def fetch_website_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        soup = BeautifulSoup(response.content, 'html.parser')  # Parse the response content
        text_content = soup.get_text()  # Get text from the parsed content
        return text_content
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching the website: {e}")
        return None

# Function to get LLM reply
def get_llm_reply(user_input, word_placeholder):
    try:
        # Initialize an empty response
        response = ""

        # Create a completion request
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Based on the HTML text given to you, understand what the website is about "
                        "and summarize the information in bullet format with insights. Keep the information accurate and clear."
                    ),
                },
                {"role": "user", "content": user_input},
            ],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=True,
            stop=None,
        )

        # Process the streaming response
        for chunk in completion:
            delta = chunk.choices[0].delta.content or ""
            response += delta
            word_placeholder.write(response)

        return response
    except Exception as e:
        if "rate limit" in str(e).lower():
            st.error("Rate limit exceeded. Please try again later.")
        else:
            st.error(f"Error generating LLM reply: {e}")
        return None

# Streamlit Interface
def main():
    st.title("SearchEZ")
    st.text("simply enter the website URL you want to summarize. (rate limit: 6000)")

    # Input for the website URL
    url = st.text_input("Enter the website URL:", "")

    # Initialize session state for the summary
    if "summary" not in st.session_state:
        st.session_state["summary"] = None

    # Button to fetch and summarize website
    if st.button("Fetch and Summarize"):
        if url:
            with st.spinner("Fetching website content..."):
                text_content = fetch_website_content(url)

            if text_content:
                # Check if we already have a cached summary for the input
                if st.session_state["summary"]:
                    st.write("Using cached summary...")
                    st.write(st.session_state["summary"])
                else:
                    with st.spinner("Generating summary..."):
                        word_placeholder = st.empty()  # Placeholder for streaming response
                        summary = get_llm_reply(text_content, word_placeholder)

                        if summary:
                            st.success("Summary generated successfully!")
                            st.session_state["summary"] = summary  # Cache the summary
                            st.write(summary)
                        else:
                            st.error("Failed to generate summary. Please try again.")
            else:
                st.error("Failed to fetch website content. Please try again.")
        else:
            st.error("Please enter a valid website URL.")

    # Debugging option (for local testing)
    if st.checkbox("Debug Mode"):
        st.write("Debug Information:")
        st.write(f"API Key: {'Set' if GROQ_API_KEY else 'Not Set'}")
        st.write(f"Rate limit error? {'Yes' if st.session_state.get('rate_limit_error', False) else 'No'}")

if __name__ == "__main__":
    main()
