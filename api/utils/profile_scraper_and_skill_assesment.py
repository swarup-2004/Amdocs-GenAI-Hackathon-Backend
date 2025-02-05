from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from linkedin_api import Linkedin
import requests
import json
import os

LINKEDIN_TOKEN = os.getenv("LINKEDIN_API_KEY")

def scrape_linkedin(name: str):
    # Note: Storing credentials in code is not recommended for production use
    api = Linkedin('tanmayiscoding@gmail.com', LINKEDIN_TOKEN)
    profile = api.get_profile(name)
    return profile

# Replace with your GitHub Personal Access Token
GITHUB_TOKEN = os.getenv("GITHUB_API_KEY")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

def fetch_github_profile(username: str):
    try:
        user_url = f"https://api.github.com/users/{username}"
        repos_url = f"https://api.github.com/users/{username}/repos?per_page=100&page=1"

        # Fetch user profile with rate limit handling
        user_response = requests.get(user_url, headers=HEADERS)
        if user_response.status_code == 403 and 'rate limit' in user_response.text:
            raise Exception("GitHub API rate limit exceeded")
        if user_response.status_code != 200:
            return None

        user_data = user_response.json()

        # Handle paginated repositories
        all_repos = []
        while repos_url:
            repos_response = requests.get(repos_url, headers=HEADERS)
            if repos_response.status_code != 200:
                break
            all_repos.extend(repos_response.json())
            repos_url = repos_response.links.get('next', {}).get('url')

        profile = {
            "name": user_data.get("name"),
            "bio": user_data.get("bio"),
            "public_repos": user_data.get("public_repos"),
            "followers": user_data.get("followers"),
            "following": user_data.get("following"),
            "languages used in bytes": {},
        }

        for repo in all_repos:
            if repo.get("fork"):
                continue

            lang_url = repo.get("languages_url")
            lang_response = requests.get(lang_url, headers=HEADERS)
            if lang_response.status_code != 200:
                continue

            langs = lang_response.json()
            for lang, bytes_of_code in langs.items():
                profile["languages used in bytes"][lang] = (
                    profile["languages used in bytes"].get(lang, 0) + bytes_of_code
                )

        return profile

    except Exception as e:
        print(f"Error fetching GitHub profile: {e}")
        return None

# Example usage
github_profile = fetch_github_profile("decodingafterlife")
linkedin_profile = scrape_linkedin('tanmay-shingavi')

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
chat = ChatGroq(temperature=0, groq_api_key=GROQ_API_KEY, model_name="deepseek-r1-distill-llama-70b")

def assess_skills(linkedin_profile: dict, github_profile: dict) -> dict:
    analysis_template = """
    Analyze the following professional profiles and provide a comprehensive skill assessment:
    
    LinkedIn Profile:
    {linkedin_profile}
    
    GitHub Profile:
    {github_profile}
    
    Perform the following analysis:
    1. Extract all technical and professional skills from both profiles
    2. Categorize skills into domains (e.g., Programming Languages, Frameworks, Tools)
    3. Assign Bloom's Taxonomy levels based on evidence of mastery:
       - Remember: Basic understanding/recall
       - Understand: Comprehension of concepts
       - Apply: Practical implementation
       - Analyze: Complex problem-solving
       - Evaluate: Critical assessment
       - Create: Original development
    4. Identify skill gaps based on industry standards
    5. Provide recommendations for skill development
    
    {format_instructions}
    
    Assessment Guidelines:
    - Consider code volume and project complexity from GitHub
    - Analyze work experience duration and responsibilities from LinkedIn
    - Evaluate education and certifications
    - Compare with current industry requirements
    - Account for demonstrated project work
    """

    # Response schemas
    response_schemas = [
        ResponseSchema(name="user_name", description="Combined name from profiles"),
        ResponseSchema(name="categorized_skills", 
                      description="List of skills with category and Bloom's level",
                      type="array",
                      items={
                          "type": "object",
                          "properties": {
                              "skill_name": {"type": "string"},
                              "category": {"type": "string"},
                              "bloom_level": {"type": "string", 
                                            "enum": ["Remember", "Understand", "Apply", 
                                                    "Analyze", "Evaluate", "Create"]},
                              "evidence_source": {"type": "string"},
                              "confidence_score": {"type": "number"}
                          }
                      }),
        ResponseSchema(name="skill_gaps", 
                      description="Missing skills expected for the profile level",
                      type="array",
                      items={"type": "string"}),
        ResponseSchema(name="recommendations", 
                      description="Personalized development recommendations",
                      type="array",
                      items={"type": "string"})
    ]

    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()

    prompt = ChatPromptTemplate.from_template(template=analysis_template)
    
    message = prompt.format_messages(
        linkedin_profile=str(linkedin_profile),
        github_profile=str(github_profile),
        format_instructions=format_instructions
    )
    
    response = chat.invoke(message)
    return output_parser.parse(response.content)

# Example usage:
def skills(linkedin_profile, github_profile):
    return assess_skills(linkedin_profile, github_profile)
