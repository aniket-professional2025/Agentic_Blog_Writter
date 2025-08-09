# Importing Required Packages
from agno.agent import Agent
from agno.models.google import Gemini
import re
import pandas as pd
import markdown
from datetime import datetime
import os

# Prompt to generate blog metadata
metadata_prompt = '''You are an expert skincare content strategist. Your task is to generate a JSON object containing blog ideas in both English and Hindi for a skincare website.
Please return the data in the following format:
{
  "englishTitle": "TITLE IN ENGLISH",
  "hindiTitle": "TITLE IN HINDI (in Devanagari script)",
  "englishSeoFriendlyKeyword": "SEO KEYWORDS IN ENGLISH (comma-separated)",
  "hindiSeoFriendlyKeyword": "SEO KEYWORDS IN HINDI (in Devanagari script, comma-separated)"
}
The blog ideas should be:
- Highly relevant to trending skincare concerns
- Useful for people in India
- Focused on natural remedies, routines, product recommendations, or seasonal skincare
Give only one JSON object in response.
'''

# Set up the agent
agent = Agent(model=Gemini(id="gemini-2.0-flash-exp"), markdown=False)

# Define function to get The Response
def get_prompt_response(prompt: str) -> str:
    stream = agent.run(prompt, stream=True, stream_intermediate_steps=True)
    response = ""
    for event in stream:
        if event.event == "RunResponseContent":
            response += event.content
    return response

# Function to Extract Metadata of the Blog
def extract_blog_metadata(response: str):
    return {
        "englishTitle": re.search(r'"englishTitle":\s*"([^"]+)"', response).group(1),
        "hindiTitle": re.search(r'"hindiTitle":\s*"([^"]+)"', response).group(1),
        "englishSeoFriendlyKeyword": re.search(r'"englishSeoFriendlyKeyword":\s*"([^"]+)"', response).group(1),
        "hindiSeoFriendlyKeyword": re.search(r'"hindiSeoFriendlyKeyword":\s*"([^"]+)"', response).group(1),
    }

# Function to Generate English Blog
def generateEnglishBlog(title: str, keywords: str) -> dict:
    prompt = f"Write a skincare blog in English with the title '{title}' using the keywords: {keywords}. Format it using Markdown with headings, bullet points, bold, etc."
    content = get_prompt_response(prompt).strip()
    html_content = markdown.markdown(content)
    return {
        "blogContent": content,
        "blogMarkup": html_content
    }

# Function to Generate Hindi Blog
def generateHindiBlog(title: str, keywords: str) -> dict:
    prompt = f"Write a skincare blog in **Hindi** with the title '{title}' using the keywords: {keywords}. Format it using Markdown with headings, bullet points, bold, etc."
    content = get_prompt_response(prompt).strip()
    html_content = markdown.markdown(content)
    return {
        "blogContent": content,
        "blogMarkup": html_content
    }

# === Generate and Append Blog ===

# Step 1: Get metadata
jsonResponse = get_prompt_response(metadata_prompt)
metadata = extract_blog_metadata(jsonResponse)

# Step 2: Generate blogs
english_blog = generateEnglishBlog(metadata["englishTitle"], metadata["englishSeoFriendlyKeyword"])
hindi_blog = generateHindiBlog(metadata["hindiTitle"], metadata["hindiSeoFriendlyKeyword"])

# Step 3: Prepare row data
now = datetime.now()
timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

new_row = {
    "Date Time": timestamp,
    "English Title": metadata["englishTitle"],
    "Hindi Title": metadata["hindiTitle"],
    "English Keywords": metadata["englishSeoFriendlyKeyword"],
    "Hindi Keywords": metadata["hindiSeoFriendlyKeyword"],
    "English Blog Content (Markdown)": english_blog["blogContent"],
    "Hindi Blog Content (Markdown)": hindi_blog["blogContent"],
    "English Blog HTML": english_blog["blogMarkup"],
    "Hindi Blog HTML": hindi_blog["blogMarkup"],
}

# Step 4: File operations
output_file = "skincare_blogs.xlsx"
columns = list(new_row.keys())

if os.path.exists(output_file):
    existing_df = pd.read_excel(output_file, engine="openpyxl")
    df = pd.concat([existing_df, pd.DataFrame([new_row])], ignore_index=True)
else:
    df = pd.DataFrame([new_row], columns=columns)

# Step 5: Save
df.to_excel(output_file, index=False, engine="openpyxl")
print(f"Blog added to: {output_file} at {timestamp}")
