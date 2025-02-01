from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import os
import dotenv
from langchain_community.vectorstores import Neo4jVector
from langchain.chains import RetrievalQAWithSourcesChain
from langchain_community.graphs import Neo4jGraph
import neo4j
from neo4j import GraphDatabase
import requests
from linkedin_api import Linkedin
from langchain_groq import ChatGroq
from langchain_community.vectorstores import Neo4jVector

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
chat = ChatGroq(temperature=0, groq_api_key=GROQ_API_KEY, model_name="deepseek-r1-distill-llama-70b")

AVAILABLE_SKILLS = [
    # Original AIML Skills
    'Python',
    'Machine Learning',
    'Deep Learning',
    'Statistics',
    'Data Analysis',
    'TensorFlow/PyTorch',
    
    # New AIML Skills
    'Computer Vision',
    'Natural Language Processing',
    'Data Visualization',
    'Experimental Design',
    'Feature Engineering',
    'Model Deployment',
    
    # Original Web Development Skills
    'HTML/CSS',
    'JavaScript',
    'React/Angular/Vue',
    'Node.js',
    'Database Management',
    'REST APIs',
    
    # New Web Development Skills
    'TypeScript',
    'Web Security',
    'Web Performance Optimization',
    'Responsive Design',
    'Testing (Unit/Integration)',
    'CI/CD',
    
    # Original Cybersecurity Skills
    'Network Security',
    'Ethical Hacking',
    'Cryptography',
    'SIEM Tools',
    'Compliance (GDPR, HIPAA)',
    'Linux/Unix',
    
    # New Cybersecurity Skills
    'Shell Scripting',
    'Digital Forensics',
    'Malware Analysis',
    'Incident Response',
    'Penetration Testing',
    'Risk Management',
    
    # Original Cloud Engineering Skills
    'AWS',
    'Azure',
    'Docker/Kubernetes',
    'Terraform',
    'Cloud Networking',
    'Serverless Architecture',
    
    # New Cloud Engineering Skills
    'Cloud Security',
    'Cloud Monitoring',
    'Multi-cloud Architecture',
    'Microservices',
    'Cloud Cost Optimization',
    'Load Balancing'

    'C++',
    'Shell',
    'C',
    'Jupyter Notebook',
    'JavaScript',
    'TypeScript'
]

TARGET_ROLES = ['Artificial Intelligence/Machine Learning Engineer',
                'Web Developer', 'Cybersecurity Specialist', 'Cloud Engineer']

def clean_text(text):
    """Remove emojis and special characters from text."""
    return ''.join(c for c in text if c.isalnum() or c in ' ,@|')

def get_primary_skills(languages_used):
    """Extract primary skills based on language usage."""
    if not languages_used:
        return []
    
    # Convert bytes to percentages and sort by usage
    total_bytes = sum(languages_used.values())
    language_percentages = {
        lang: (bytes_used / total_bytes) * 100 
        for lang, bytes_used in languages_used.items()
    }
    
    # Return languages that match our available skills
    return language_percentages.keys() & set(AVAILABLE_SKILLS)

def extract_profile_data(linkedin_profile, github_profile):
    """Extract and format profile data from the specific profile formats."""
    profile_data = {
        'firstName': linkedin_profile.get('firstName', ''),
        'lastName': linkedin_profile.get('lastName', ''),
        'location': linkedin_profile.get('locationName', ''),
        'industry': 'Technology',  # Default since no industry in profile
        'headline': clean_text(linkedin_profile.get('headline', '')),
        'githubName': github_profile.get('name', ''),
        'publicRepos': github_profile.get('public_repos', 0),
        'followers': github_profile.get('followers', 0),
        'following': github_profile.get('following', 0)
    }
    
    # Extract skills from GitHub languages
    profile_data['primary_skills'] = get_primary_skills(
        github_profile.get('languages used in bytes', {})
    )
    
    return profile_data

def create_cypher_queries(profile_data, target_role):
    """Create Cypher queries using the extracted profile data."""
    # Create user node query
    user_node_query = f"""
MERGE (u:User {{
    name: '{profile_data["firstName"]}',
    lastName: '{profile_data["lastName"]}',
    locationName: '{profile_data["location"]}',
    industryName: '{profile_data["industry"]}',
    headline: '{profile_data["headline"]}',
    github: '{profile_data["githubName"]}',
    public_repos: {profile_data["publicRepos"]},
    followers: {profile_data["followers"]},
    following: {profile_data["following"]}
}})"""

    # Create skill relationship queries
    skill_queries = []
    for skill in profile_data['primary_skills']:
        skill_query = f"""
WITH u
MATCH (u:User), (s:Skill {{name: '{skill}'}})
WHERE u.name = '{profile_data["firstName"]}' AND u.lastName = '{profile_data["lastName"]}'
MERGE (u)-[:HAS_SKILL {{proficiency: 100, bloom_level: 'Create'}}]->(s)"""
        skill_queries.append(skill_query)

    # Create goal relationship query
    goal_query = f"""
WITH DISTINCT u
MATCH (u:User), (j:JobRole {{title: '{target_role}'}})
WHERE u.name = '{profile_data["firstName"]}' AND u.lastName = '{profile_data["lastName"]}'
MERGE (u)-[:TARGETS]->(j)"""

    return {
        "user_node": user_node_query,
        "skill_relationships": skill_queries,
        "goal_relationship": goal_query
    }

def determine_target_role(user_goal, target_roles):
    """
    Match user's career goal with the closest target role using fuzzy string matching.
    
    Parameters:
    user_goal (str): The user's entered career goal
    target_roles (list): List of available target roles
    
    Returns:
    tuple: Best matching role and its match score
    """
    # Clean the input by removing common phrases that might affect matching
    clean_goal = user_goal.lower().replace("i want to become", "").replace("i want to be", "").strip()
    
    # Use process.extractOne to find the best match
    best_match = process.extractOne(
        clean_goal,
        target_roles,
        scorer=fuzz.token_sort_ratio  # Uses token sort ratio for better partial matching
    )
    
    return best_match[0]  # Returns (matched_role, score)

def generate_cypher(linkedin_profile, github_profile, user_goal, chat):
    """
    Generate Cypher queries from LinkedIn and GitHub profiles.
    
    Args:
        linkedin_profile (dict): LinkedIn profile data in the specified format
        github_profile (dict): GitHub profile data in the specified format
        user_goal (str): User's career goal
        chat: Chat model instance
    
    Returns:
        str: Combined Cypher queries
    """
    try:
        # Extract and format profile data
        profile_data = extract_profile_data(linkedin_profile, github_profile)
        
        # Determine target role based on user goal and skills
        target_role = determine_target_role(user_goal, TARGET_ROLES)
        
        # Generate Cypher queries
        queries = create_cypher_queries(profile_data, target_role)
        
        # Combine all queries
        all_queries = [
            queries["user_node"],
            *queries["skill_relationships"],
            queries["goal_relationship"]
        ]
        
        return "\n".join(all_queries)
    
    except Exception as e:
        raise Exception(f"Error generating Cypher queries: {str(e)}")

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

kg = Neo4jGraph(
    url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD, database='neo4j'
)

LINKEDIN_TOKEN = os.getenv("LINKEDIN_API_KEY")

def scrape_linkedin(name: str):
    # Note: Storing credentials in code is not recommended for production use
    api = Linkedin('tanmayspaln@gmail.com', 'Amdocs@2025*')
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
linkedin_profile = linkedin_profile = {
    "industryName": "Computer Software",
    "lastName": "Shingavi",
    "locationName": "India",
    "student": "false",
    "geoCountryName": "India",
    "geoCountryUrn": "urn:li:fs_geo:102713980",
    "geoLocationBackfilled": "false",
    "elt": "false",
    "industryUrn": "urn:li:fs_industry:4",
    "firstName": "Tanmay",
    "entityUrn": "urn:li:fs_profile:ACoAADHw9bMB-2gciyGcmP8-r3yofwScuijK9Mc",
    "geoLocation": {
        "geoUrn": "urn:li:fs_geo:105527523"
    },
    "geoLocationName": "Pune, Maharashtra",
    "location": {
        "basicLocation": {
            "countryCode": "in"
        }
    },
    "headline": "\ud83d\udcbbIntern @SynapseHealthtech | \ud83d\udc68\ud83c\udffb\u200d\ud83d\udcbb Junior ML Engineer and Open Source Contributor @Omdena | \ud83e\udd35\ud83c\udffb\u200d\u2642\ufe0f Vice Chairman @PICT CYBERCELL | \ud83c\udfc6 3x Hackathon Winner",
    "displayPictureUrl": "https://media.licdn.com/dms/image/v2/D4D35AQG2XGHcM9xYaw/profile-framedphoto-shrink_",
    "img_400_400": "400_400/profile-framedphoto-shrink_400_400/0/1683782719125?e=1737439200&v=beta&t=xEuJGietXDpwL102R6alyumn5EQ7a84Z_4NTDeeW4Uo",
    "img_200_200": "200_200/profile-framedphoto-shrink_200_200/0/1683782719125?e=1737439200&v=beta&t=CLj0lfWsHyIboT51OMpkim8dKnTZILzLSeW98bJkNv0",
    "img_800_800": "800_800/profile-framedphoto-shrink_800_800/0/1683782719125?e=1737439200&v=beta&t=KFnNKAphanBw5PXRORrmtOC_HtpsvheaCZZYKWj1kgA",
    "img_100_100": "100_100/profile-framedphoto-shrink_100_100/0/1683782719125?e=1737439200&v=beta&t=sMKkldjCFqxqw2dnuQGOglBs-Ew4Ae6W80jjPbsxP4E",
    "profile_id": "ACoAADHw9bMB-2gciyGcmP8-r3yofwScuijK9Mc",
    "profile_urn": "urn:li:fs_miniProfile:ACoAADHw9bMB-2gciyGcmP8-r3yofwScuijK9Mc",
    "member_urn": "urn:li:member:837875123",
    "public_id": "tanmay-shingavi",
    "experience": [
        {
            "entityUrn": "urn:li:fs_position:(ACoAADHw9bMB-2gciyGcmP8-r3yofwScuijK9Mc,2543872663)",
            "companyName": "SynapseHealthTech (Synapse Analytics IT Services)",
            "timePeriod": {
                "startDate": {
                    "month": 12,
                    "year": 2024
                }
            },
            "company": {
                "employeeCountRange": {
                    "start": 11,
                    "end": 50
                },
                "industries": [
                    "Information Technology and Services"
                ]
            },
            "title": "Data Scientist Intern",
            "companyUrn": "urn:li:fs_miniCompany:95044103",
            "companyLogoUrl": "https://media.licdn.com/dms/image/v2/D4D0BAQFPY43UHbcU1A/company-logo_"
        },
        {
            "entityUrn": "urn:li:fs_position:(ACoAADHw9bMB-2gciyGcmP8-r3yofwScuijK9Mc,2490503614)",
            "companyName": "PICT Finance Society",
            "timePeriod": {
                "startDate": {
                    "month": 10,
                    "year": 2024
                }
            },
            "company": {
                "employeeCountRange": {
                    "start": 11,
                    "end": 50
                },
                "industries": [
                    "Nonprofit Organization Management"
                ]
            },
            "title": "Content & Research Team Head",
            "companyUrn": "urn:li:fs_miniCompany:101065462",
            "companyLogoUrl": "https://media.licdn.com/dms/image/v2/D4D0BAQEHmOWzqzbbYg/company-logo_"
        },
        {
            "entityUrn": "urn:li:fs_position:(ACoAADHw9bMB-2gciyGcmP8-r3yofwScuijK9Mc,2523582620)",
            "companyName": "PICT CyberCell",
            "timePeriod": {
                "startDate": {
                    "month": 8,
                    "year": 2024
                }
            },
            "company": {
                "employeeCountRange": {
                    "start": 11,
                    "end": 50
                },
                "industries": [
                    "Computer & Network Security"
                ]
            },
            "title": "Vice Chairperson ",
            "companyUrn": "urn:li:fs_miniCompany:98368472",
            "companyLogoUrl": "https://media.licdn.com/dms/image/v2/D4E0BAQGu9LCwpy9hdw/company-logo_"
        },
        {
            "locationName": "Pune, Maharashtra, India",
            "entityUrn": "urn:li:fs_position:(ACoAADHw9bMB-2gciyGcmP8-r3yofwScuijK9Mc,2230815152)",
            "geoLocationName": "Pune, Maharashtra, India",
            "geoUrn": "urn:li:fs_geo:114806696",
            "companyName": "PICT Model United Nations",
            "timePeriod": {
                "startDate": {
                    "month": 3,
                    "year": 2024
                }
            },
            "company": {
                "employeeCountRange": {
                    "start": 11,
                    "end": 50
                },
                "industries": [
                    "Civic & Social Organization"
                ]
            },
            "title": "USG Technical Affairs",
            "region": "urn:li:fs_region:(in,0)",
            "companyUrn": "urn:li:fs_miniCompany:81467605",
            "companyLogoUrl": "https://media.licdn.com/dms/image/v2/C4E0BAQE3BysfPL3gxQ/company-logo_"
        },
        {
            "entityUrn": "urn:li:fs_position:(ACoAADHw9bMB-2gciyGcmP8-r3yofwScuijK9Mc,2201892567)",
            "companyName": "Edc pict",
            "timePeriod": {
                "startDate": {
                    "month": 1,
                    "year": 2023
                }
            },
            "title": "Member"
        }
    ],
    "education": [
        {
            "projects": [
                "urn:li:fs_project:(ACoAADHw9bMB-2gciyGcmP8-r3yofwScuijK9Mc,1873965634)"
            ],
            "entityUrn": "urn:li:fs_education:(ACoAADHw9bMB-2gciyGcmP8-r3yofwScuijK9Mc,877324677)",
            "school": {
                "objectUrn": "urn:li:school:20970",
                "entityUrn": "urn:li:fs_miniSchool:20970",
                "active": "true",
                "schoolName": "Pune Institute of Computer Technology",
                "trackingId": "FQW1lAyMSYe12+Th5MO+Bg==",
                "logoUrl": "https://media.licdn.com/dms/image/v2/C560BAQFMx5qjAC9X-w/company-logo_"
            },
            "activities": "PICTOREAL | EDC | DEBSOC |GDU | ART CIRCLE",
            "grade": "Be computer engineer",
            "timePeriod": {
                "endDate": {
                    "month": 4,
                    "year": 2026
                },
                "startDate": {
                    "month": 11,
                    "year": 2022
                }
            },
            "fieldOfStudyUrn": "urn:li:fs_fieldOfStudy:100347",
            "degreeName": "Bachelor's degree",
            "schoolName": "Pune Institute of Computer Technology",
            "fieldOfStudy": "Computer Engineering",
            "schoolUrn": "urn:li:fs_miniSchool:20970"
        },
        {
            "entityUrn": "urn:li:fs_education:(ACoAADHw9bMB-2gciyGcmP8-r3yofwScuijK9Mc,671563663)",
            "school": {
                "objectUrn": "urn:li:school:3245177",
                "entityUrn": "urn:li:fs_miniSchool:3245177",
                "active": "true",
                "schoolName": "St. Vincent's High School",
                "trackingId": "VHBQwQUESjS2UgQeK8kybg==",
                "logoUrl": "https://media.licdn.com/dms/image/v2/C510BAQGZYB17BNja6w/company-logo_"
            },
            "timePeriod": {
                "endDate": {
                    "year": 2020
                },
                "startDate": {
                    "year": 2010
                }
            },
            "schoolName": "St. Vincent's High School",
            "schoolUrn": "urn:li:fs_miniSchool:3245177"
        }
    ],
    "languages": [],
    "publications": [],
    "certifications": [],
    "volunteer": [],
    "honors": [],
    "projects": [
        {
            "occupation": "urn:li:fs_position:(ACoAADHw9bMB-2gciyGcmP8-r3yofwScuijK9Mc,2153975752)",
            "members": [
                {
                    "member": {
                        "firstName": "Tanmay",
                        "lastName": "Shingavi",
                        "dashEntityUrn": "urn:li:fsd_profile:ACoAADHw9bMB-2gciyGcmP8-r3yofwScuijK9Mc",
                        "occupation": "\ud83d\udcbbIntern @SynapseHealthtech | \ud83d\udc68\ud83c\udffb\u200d\ud83d\udcbb Junior ML Engineer and Open Source Contributor @Omdena | \ud83e\udd35\ud83c\udffb\u200d\u2642\ufe0f Vice Chairman @PICT CYBERCELL | \ud83c\udfc6 3x Hackathon Winner",
                        "objectUrn": "urn:li:member:837875123",
                        "entityUrn": "urn:li:fs_miniProfile:ACoAADHw9bMB-2gciyGcmP8-r3yofwScuijK9Mc",
                        "publicIdentifier": "tanmay-shingavi",
                        "picture": {
                            "com.linkedin.common.VectorImage": {
                                "artifacts": [
                                    {
                                        "width": 400,
                                        "fileIdentifyingUrlPathSegment": "400_400/profile-framedphoto-shrink_400_400/0/1683782719125?e=1737439200&v=beta&t=xEuJGietXDpwL102R6alyumn5EQ7a84Z_4NTDeeW4Uo",
                                        "expiresAt": 1737439200000,
                                        "height": 400
                                    },
                                    {
                                        "width": 200,
                                        "fileIdentifyingUrlPathSegment": "200_200/profile-framedphoto-shrink_200_200/0/1683782719125?e=1737439200&v=beta&t=CLj0lfWsHyIboT51OMpkim8dKnTZILzLSeW98bJkNv0",
                                        "expiresAt": 1737439200000,
                                        "height": 200
                                    },
                                    {
                                        "width": 800,
                                        "fileIdentifyingUrlPathSegment": "800_800/profile-framedphoto-shrink_800_800/0/1683782719125?e=1737439200&v=beta&t=KFnNKAphanBw5PXRORrmtOC_HtpsvheaCZZYKWj1kgA",
                                        "expiresAt": 1737439200000,
                                        "height": 800
                                    },
                                    {
                                        "width": 100,
                                        "fileIdentifyingUrlPathSegment": "100_100/profile-framedphoto-shrink_100_100/0/1683782719125?e=1737439200&v=beta&t=sMKkldjCFqxqw2dnuQGOglBs-Ew4Ae6W80jjPbsxP4E",
                                        "expiresAt": 1737439200000,
                                        "height": 100
                                    }
                                ],
                                "rootUrl": "https://media.licdn.com/dms/image/v2/D4D35AQG2XGHcM9xYaw/profile-framedphoto-shrink_"
                            }
                        },
                        "trackingId": "umguI1UHR3a1T6x5mrNjTw=="
                    },
                    "entityUrn": "urn:li:fs_contributor:(ACoAADHw9bMB-2gciyGcmP8-r3yofwScuijK9Mc,543373760,428448292)",
                    "profileUrn": "urn:li:fs_miniProfile:ACoAADHw9bMB-2gciyGcmP8-r3yofwScuijK9Mc"
                },
                {
                    "member": {
                        "firstName": "Swarup",
                        "lastName": "Pokharkar",
                        "dashEntityUrn": "urn:li:fsd_profile:ACoAADdNuh4B2q-qTMPz9k6JIVcvf88R2MIl6OI",
                        "occupation": "Building Solutions | Upcoming Summer Intern @ BNY Mellon | Member @ PASC | PICT '26",
                        "objectUrn": "urn:li:member:927840798",
                        "entityUrn": "urn:li:fs_miniProfile:ACoAADdNuh4B2q-qTMPz9k6JIVcvf88R2MIl6OI",
                        "backgroundImage": {
                            "com.linkedin.common.VectorImage": {
                                "artifacts": [
                                    {
                                        "width": 800,
                                        "fileIdentifyingUrlPathSegment": "200_800/profile-displaybackgroundimage-shrink_200_800/0/1732978010989?e=1742428800&v=beta&t=1MrdL71YLLLn1HIQL_zG5wbVQoyTmeLb1TN0t0ejW2Y",
                                        "expiresAt": 1742428800000,
                                        "height": 200
                                    },
                                    {
                                        "width": 1400,
                                        "fileIdentifyingUrlPathSegment": "350_1400/profile-displaybackgroundimage-shrink_350_1400/0/1732978010989?e=1742428800&v=beta&t=Oz8KYX7Q2z2OclSh0RjIA52hdgvKgIpUj-D6auLW9Kw",
                                        "expiresAt": 1742428800000,
                                        "height": 350
                                    }
                                ],
                                "rootUrl": "https://media.licdn.com/dms/image/v2/D4D16AQHPRUEZFV76cw/profile-displaybackgroundimage-shrink_"
                            }
                        },
                        "publicIdentifier": "swarup-pokharkar",
                        "picture": {
                            "com.linkedin.common.VectorImage": {
                                "artifacts": [
                                    {
                                        "width": 100,
                                        "fileIdentifyingUrlPathSegment": "100_100/profile-displayphoto-shrink_100_100/0/1728156168667?e=1742428800&v=beta&t=lFmopxoZNJlyyAqOSOMUN8a3JzRt-2MpGxo6A5QVWpI",
                                        "expiresAt": 1742428800000,
                                        "height": 100
                                    },
                                    {
                                        "width": 200,
                                        "fileIdentifyingUrlPathSegment": "200_200/profile-displayphoto-shrink_200_200/0/1728156168667?e=1742428800&v=beta&t=N73QOBJx0v_SvvDFyllS13vWNPpY_V35wtxOqsecvLs",
                                        "expiresAt": 1742428800000,
                                        "height": 200
                                    },
                                    {
                                        "width": 400,
                                        "fileIdentifyingUrlPathSegment": "400_400/profile-displayphoto-shrink_400_400/0/1728156168667?e=1742428800&v=beta&t=z1mkFCo0Y40GhnAqRUST3bOPt93RP77Q35ZUDblQJHU",
                                        "expiresAt": 1742428800000,
                                        "height": 400
                                    },
                                    {
                                        "width": 800,
                                        "fileIdentifyingUrlPathSegment": "800_800/profile-displayphoto-shrink_800_800/0/1728156168692?e=1742428800&v=beta&t=8rPEIx7BQOkHAbQ05ei28K2MvKEZfniWkTbmC3xMf3k",
                                        "expiresAt": 1742428800000,
                                        "height": 800
                                    }
                                ],
                                "rootUrl": "https://media.licdn.com/dms/image/v2/D4D03AQGJfpJKlRATiw/profile-displayphoto-shrink_"
                            }
                        },
                        "trackingId": "3HPjAdbeRc++PHRdmlDDAQ=="
                    },
                    "entityUrn": "urn:li:fs_contributor:(ACoAADHw9bMB-2gciyGcmP8-r3yofwScuijK9Mc,543373760,428442908)",
                    "profileUrn": "urn:li:fs_miniProfile:ACoAADdNuh4B2q-qTMPz9k6JIVcvf88R2MIl6OI"
                },
                {
                    "member": {
                        "firstName": "Atharva",
                        "lastName": "Zanjad",
                        "dashEntityUrn": "urn:li:fsd_profile:ACoAAECX2wYBxKcRYUYmODBSpe0-CoM1bJG5R38",
                        "occupation": "PICT '26 | \u2b50\u2b50\u2b50 @Codechef | Front-End Developer",
                        "objectUrn": "urn:li:member:1083693830",
                        "entityUrn": "urn:li:fs_miniProfile:ACoAAECX2wYBxKcRYUYmODBSpe0-CoM1bJG5R38",
                        "publicIdentifier": "atharva-zanjad-odin5133",
                        "trackingId": "FfPmr3I8RtSvbj9bxKMS5Q=="
                    },
                    "entityUrn": "urn:li:fs_contributor:(ACoAADHw9bMB-2gciyGcmP8-r3yofwScuijK9Mc,543373760,428442909)",
                    "profileUrn": "urn:li:fs_miniProfile:ACoAAECX2wYBxKcRYUYmODBSpe0-CoM1bJG5R38"
                }
            ],
            "timePeriod": {
                "endDate": {
                    "month": 4,
                    "year": 2024
                },
                "startDate": {
                    "month": 1,
                    "year": 2024
                }
            },
            "description": "This project focuses on utilizing machine learning techniques to identify various medicinal plants and provide users with relevant information. Below are the key components of the project:\n\nCNN Model Training: We have trained a Convolutional Neural Network (CNN) model using TensorFlow and Keras. The model is trained on a dataset containing images of medicinal plants.\n\nFlask API: To deploy the trained model and make predictions accessible, we have built a Flask API. This API serves as the interface for users to interact with the model.\n\nPlant Classes: The model can successfully identify images belonging to six different classes of medicinal plants. These classes are:\n\nArjuna\n\nBramhi\n\nCurry\n\nMint\n\nNeem\n\nRubble\n\nPrediction and Information Retrieval:\n\nUpon successful prediction, users receive information about the identified medicinal plant. This information includes various attributes such as medicinal properties, usage, and precautions.\n\nChatbot Integration: Additionally, we have integrated a chatbot feature to allow users to ask questions related to the identified plant. The chatbot provides informative responses based on the user's queries.",
            "title": "Flora Vision"
        },
        {
            "occupation": "urn:li:fs_education:(ACoAADHw9bMB-2gciyGcmP8-r3yofwScuijK9Mc,877324677)",
            "members": [
                {
                    "member": {
                        "firstName": "Tanmay",
                        "lastName": "Shingavi",
                        "dashEntityUrn": "urn:li:fsd_profile:ACoAADHw9bMB-2gciyGcmP8-r3yofwScuijK9Mc",
                        "occupation": "\ud83d\udcbbIntern @SynapseHealthtech | \ud83d\udc68\ud83c\udffb\u200d\ud83d\udcbb Junior ML Engineer and Open Source Contributor @Omdena | \ud83e\udd35\ud83c\udffb\u200d\u2642\ufe0f Vice Chairman @PICT CYBERCELL | \ud83c\udfc6 3x Hackathon Winner",
                        "objectUrn": "urn:li:member:837875123",
                        "entityUrn": "urn:li:fs_miniProfile:ACoAADHw9bMB-2gciyGcmP8-r3yofwScuijK9Mc",
                        "publicIdentifier": "tanmay-shingavi",
                        "picture": {
                            "com.linkedin.common.VectorImage": {
                                "artifacts": [
                                    {
                                        "width": 400,
                                        "fileIdentifyingUrlPathSegment": "400_400/profile-framedphoto-shrink_400_400/0/1683782719125?e=1737439200&v=beta&t=xEuJGietXDpwL102R6alyumn5EQ7a84Z_4NTDeeW4Uo",
                                        "expiresAt": 1737439200000,
                                        "height": 400
                                    },
                                    {
                                        "width": 200,
                                        "fileIdentifyingUrlPathSegment": "200_200/profile-framedphoto-shrink_200_200/0/1683782719125?e=1737439200&v=beta&t=CLj0lfWsHyIboT51OMpkim8dKnTZILzLSeW98bJkNv0",
                                        "expiresAt": 1737439200000,
                                        "height": 200
                                    },
                                    {
                                        "width": 800,
                                        "fileIdentifyingUrlPathSegment": "800_800/profile-framedphoto-shrink_800_800/0/1683782719125?e=1737439200&v=beta&t=KFnNKAphanBw5PXRORrmtOC_HtpsvheaCZZYKWj1kgA",
                                        "expiresAt": 1737439200000,
                                        "height": 800
                                    },
                                    {
                                        "width": 100,
                                        "fileIdentifyingUrlPathSegment": "100_100/profile-framedphoto-shrink_100_100/0/1683782719125?e=1737439200&v=beta&t=sMKkldjCFqxqw2dnuQGOglBs-Ew4Ae6W80jjPbsxP4E",
                                        "expiresAt": 1737439200000,
                                        "height": 100
                                    }
                                ],
                                "rootUrl": "https://media.licdn.com/dms/image/v2/D4D35AQG2XGHcM9xYaw/profile-framedphoto-shrink_"
                            }
                        },
                        "trackingId": "umguI1UHR3a1T6x5mrNjTw=="
                    },
                    "entityUrn": "urn:li:fs_contributor:(ACoAADHw9bMB-2gciyGcmP8-r3yofwScuijK9Mc,1873965634,427245234)",
                    "profileUrn": "urn:li:fs_miniProfile:ACoAADHw9bMB-2gciyGcmP8-r3yofwScuijK9Mc"
                },
                {
                    "member": {
                        "firstName": "Swarup",
                        "lastName": "Pokharkar",
                        "dashEntityUrn": "urn:li:fsd_profile:ACoAADdNuh4B2q-qTMPz9k6JIVcvf88R2MIl6OI",
                        "occupation": "Building Solutions | Upcoming Summer Intern @ BNY Mellon | Member @ PASC | PICT '26",
                        "objectUrn": "urn:li:member:927840798",
                        "entityUrn": "urn:li:fs_miniProfile:ACoAADdNuh4B2q-qTMPz9k6JIVcvf88R2MIl6OI",
                        "backgroundImage": {
                            "com.linkedin.common.VectorImage": {
                                "artifacts": [
                                    {
                                        "width": 800,
                                        "fileIdentifyingUrlPathSegment": "200_800/profile-displaybackgroundimage-shrink_200_800/0/1732978010989?e=1742428800&v=beta&t=1MrdL71YLLLn1HIQL_zG5wbVQoyTmeLb1TN0t0ejW2Y",
                                        "expiresAt": 1742428800000,
                                        "height": 200
                                    },
                                    {
                                        "width": 1400,
                                        "fileIdentifyingUrlPathSegment": "350_1400/profile-displaybackgroundimage-shrink_350_1400/0/1732978010989?e=1742428800&v=beta&t=Oz8KYX7Q2z2OclSh0RjIA52hdgvKgIpUj-D6auLW9Kw",
                                        "expiresAt": 1742428800000,
                                        "height": 350
                                    }
                                ],
                                "rootUrl": "https://media.licdn.com/dms/image/v2/D4D16AQHPRUEZFV76cw/profile-displaybackgroundimage-shrink_"
                            }
                        },
                        "publicIdentifier": "swarup-pokharkar",
                        "picture": {
                            "com.linkedin.common.VectorImage": {
                                "artifacts": [
                                    {
                                        "width": 100,
                                        "fileIdentifyingUrlPathSegment": "100_100/profile-displayphoto-shrink_100_100/0/1728156168667?e=1742428800&v=beta&t=lFmopxoZNJlyyAqOSOMUN8a3JzRt-2MpGxo6A5QVWpI",
                                        "expiresAt": 1742428800000,
                                        "height": 100
                                    },
                                    {
                                        "width": 200,
                                        "fileIdentifyingUrlPathSegment": "200_200/profile-displayphoto-shrink_200_200/0/1728156168667?e=1742428800&v=beta&t=N73QOBJx0v_SvvDFyllS13vWNPpY_V35wtxOqsecvLs",
                                        "expiresAt": 1742428800000,
                                        "height": 200
                                    },
                                    {
                                        "width": 400,
                                        "fileIdentifyingUrlPathSegment": "400_400/profile-displayphoto-shrink_400_400/0/1728156168667?e=1742428800&v=beta&t=z1mkFCo0Y40GhnAqRUST3bOPt93RP77Q35ZUDblQJHU",
                                        "expiresAt": 1742428800000,
                                        "height": 400
                                    },
                                    {
                                        "width": 800,
                                        "fileIdentifyingUrlPathSegment": "800_800/profile-displayphoto-shrink_800_800/0/1728156168692?e=1742428800&v=beta&t=8rPEIx7BQOkHAbQ05ei28K2MvKEZfniWkTbmC3xMf3k",
                                        "expiresAt": 1742428800000,
                                        "height": 800
                                    }
                                ],
                                "rootUrl": "https://media.licdn.com/dms/image/v2/D4D03AQGJfpJKlRATiw/profile-displayphoto-shrink_"
                            }
                        },
                        "trackingId": "3HPjAdbeRc++PHRdmlDDAQ=="
                    },
                    "entityUrn": "urn:li:fs_contributor:(ACoAADHw9bMB-2gciyGcmP8-r3yofwScuijK9Mc,1873965634,427244393)",
                    "profileUrn": "urn:li:fs_miniProfile:ACoAADdNuh4B2q-qTMPz9k6JIVcvf88R2MIl6OI"
                },
                {
                    "member": {
                        "firstName": "Amey",
                        "lastName": "Joshi",
                        "dashEntityUrn": "urn:li:fsd_profile:ACoAAD8q878BV-dj-Pd8JKekGtnT40iq9cEePpo",
                        "occupation": "AI enthusiast | Competitive Coder I Flutter mobile developer | AWS, Azure cloud platforms| Linux enthusiast",
                        "objectUrn": "urn:li:member:1059779519",
                        "entityUrn": "urn:li:fs_miniProfile:ACoAAD8q878BV-dj-Pd8JKekGtnT40iq9cEePpo",
                        "publicIdentifier": "amey-joshi-3bbb02256",
                        "picture": {
                            "com.linkedin.common.VectorImage": {
                                "artifacts": [
                                    {
                                        "width": 400,
                                        "fileIdentifyingUrlPathSegment": "400_400/profile-framedphoto-shrink_400_400/0/1695000955933?e=1737439200&v=beta&t=EMQN1hEqzHF3QUhKA2ir8BFJ3uyhCESMv5B2maRLROY",
                                        "expiresAt": 1737439200000,
                                        "height": 400
                                    },
                                    {
                                        "width": 200,
                                        "fileIdentifyingUrlPathSegment": "200_200/profile-framedphoto-shrink_200_200/0/1695000955933?e=1737439200&v=beta&t=kWg6qlJe4yegMN1y8dK0xMN9kyy0dRehwJ6_qgpG1dk",
                                        "expiresAt": 1737439200000,
                                        "height": 200
                                    },
                                    {
                                        "width": 592,
                                        "fileIdentifyingUrlPathSegment": "800_800/profile-framedphoto-shrink_800_800/0/1695000955933?e=1737439200&v=beta&t=G5194esrhKAGdzmJ9a7KiXZ_nrQFCQK6t-udy9OYUQ4",
                                        "expiresAt": 1737439200000,
                                        "height": 592
                                    },
                                    {
                                        "width": 100,
                                        "fileIdentifyingUrlPathSegment": "100_100/profile-framedphoto-shrink_100_100/0/1695000955933?e=1737439200&v=beta&t=kuTzz8fN5_H461Pr2G25WN9T-lBdwzTBPISzmqjB4Yw",
                                        "expiresAt": 1737439200000,
                                        "height": 100
                                    }
                                ],
                                "rootUrl": "https://media.licdn.com/dms/image/v2/D4D35AQH_Pn3CrkmRrA/profile-framedphoto-shrink_"
                            }
                        },
                        "trackingId": "CDzqor5XRRma7xE6YVpHsA=="
                    },
                    "entityUrn": "urn:li:fs_contributor:(ACoAADHw9bMB-2gciyGcmP8-r3yofwScuijK9Mc,1873965634,427239955)",
                    "profileUrn": "urn:li:fs_miniProfile:ACoAAD8q878BV-dj-Pd8JKekGtnT40iq9cEePpo"
                },
                {
                    "member": {
                        "firstName": "Yash",
                        "lastName": "Bhoomkar",
                        "dashEntityUrn": "urn:li:fsd_profile:ACoAADX-inIBHxLY4MZp1blHiGbqaUm6bRHBKYE",
                        "occupation": "Computer Enthusiast ! Currently looking for internship opportunities!",
                        "objectUrn": "urn:li:member:905874034",
                        "entityUrn": "urn:li:fs_miniProfile:ACoAADX-inIBHxLY4MZp1blHiGbqaUm6bRHBKYE",
                        "backgroundImage": {
                            "com.linkedin.common.VectorImage": {
                                "artifacts": [
                                    {
                                        "width": 800,
                                        "fileIdentifyingUrlPathSegment": "200_800/profile-displaybackgroundimage-shrink_200_800/0/1674373303196?e=1742428800&v=beta&t=1C0txBw7YvXNOdiPD6R7poVvmGKiT5hstlpnwze4E1U",
                                        "expiresAt": 1742428800000,
                                        "height": 200
                                    },
                                    {
                                        "width": 1400,
                                        "fileIdentifyingUrlPathSegment": "350_1400/profile-displaybackgroundimage-shrink_350_1400/0/1674373303196?e=1742428800&v=beta&t=SE2xy9Osx_jvmNhcUSvE4D9fDGvI2jg6gtYZljgWoo4",
                                        "expiresAt": 1742428800000,
                                        "height": 350
                                    }
                                ],
                                "rootUrl": "https://media.licdn.com/dms/image/v2/D4D16AQHsWtjxm6g-JQ/profile-displaybackgroundimage-shrink_"
                            }
                        },
                        "publicIdentifier": "yash-bhoomkar-7aa460213",
                        "picture": {
                            "com.linkedin.common.VectorImage": {
                                "artifacts": [
                                    {
                                        "width": 400,
                                        "fileIdentifyingUrlPathSegment": "400_400/profile-framedphoto-shrink_400_400/0/1719451865342?e=1737439200&v=beta&t=_K2wf5k1hBub5nnLVGKvjjpxpuVVCsXdkjLqI5lnMEo",
                                        "expiresAt": 1737439200000,
                                        "height": 400
                                    },
                                    {
                                        "width": 200,
                                        "fileIdentifyingUrlPathSegment": "200_200/profile-framedphoto-shrink_200_200/0/1719450402237?e=1737439200&v=beta&t=NYKub1SfnVmMtAschM1GgfCr2uCXnNclL_dKbzWgD78",
                                        "expiresAt": 1737439200000,
                                        "height": 200
                                    },
                                    {
                                        "width": 720,
                                        "fileIdentifyingUrlPathSegment": "800_800/profile-framedphoto-shrink_800_800/0/1719451401892?e=1737439200&v=beta&t=UK7AGL_y44ITUrwBMo869SpOPrksFvAx6eaTAblmCKs",
                                        "expiresAt": 1737439200000,
                                        "height": 720
                                    },
                                    {
                                        "width": 100,
                                        "fileIdentifyingUrlPathSegment": "100_100/profile-framedphoto-shrink_100_100/0/1719449251471?e=1737439200&v=beta&t=kjVn3mJKgP9NIcQT0MYENg4mDKJp4_5v7aZlc5bV-ms",
                                        "expiresAt": 1737439200000,
                                        "height": 100
                                    }
                                ],
                                "rootUrl": "https://media.licdn.com/dms/image/v2/D5635AQECxvlmIx7tGQ/profile-framedphoto-shrink_"
                            }
                        },
                        "trackingId": "jnGx0H9lTuyfPxenwytTrw=="
                    },
                    "entityUrn": "urn:li:fs_contributor:(ACoAADHw9bMB-2gciyGcmP8-r3yofwScuijK9Mc,1873965634,427241861)",
                    "profileUrn": "urn:li:fs_miniProfile:ACoAADX-inIBHxLY4MZp1blHiGbqaUm6bRHBKYE"
                }
            ],
            "timePeriod": {
                "endDate": {
                    "month": 2,
                    "year": 2024
                },
                "startDate": {
                    "month": 1,
                    "year": 2024
                }
            },
            "description": "Sentiment Hub is a sentiment analysis tool designed to analyze emotions expressed in text comments on YouTube and Instagram. With the ability to detect six different emotions, it provides valuable insights into audience reactions and sentiment trends across these platforms.\n\nKey features:\n\n->Analyze sentiment across YouTube and Instagram comments.\n\n->Detect six different emotions: happiness, sadness, anger, fear, surprise, and disgust.\n\n->Easy-to-use Chrome Extension that automatically detects that you are on a social media site and analyses Post and comments\n\n->User-friendly interface for input and visualization of results.\n\n->Data visualization of analysing emotions in Pie-charts, wordClouds, etc..\n\n->Target based analysis on specific inputs",
            "title": "Sentiment Hub"
        }
    ],
    "skills": [
        {
            "name": "Tenserflow "
        },
        {
            "name": "Deep Learning"
        },
        {
            "name": "Computer Vision"
        },
        {
            "name": "Front-End Development"
        }
    ],
    "urn_id": "ACoAADHw9bMB-2gciyGcmP8-r3yofwScuijK9Mc"
}

def create_knowledge_graph(linkedin_profile, github_profile, user_goal, chat):
    """
    Create a knowledge graph based on user profiles and career goal.
    
    Args:
        linkedin_profile (dict): LinkedIn profile data in the specified format
        github_profile (dict): GitHub profile data in the specified format
        user_goal (str): User's career goal
        chat: Chat model instance
    
    Returns:
        dict: Response containing the success status and any error message
    """
    try:
        # Generate Cypher queries
        cypher_queries = generate_cypher(linkedin_profile, github_profile, user_goal, chat)
        
        print(cypher_queries)

        # Execute Cypher queries
        kg.query(cypher_queries)
        
        return {"success": True, "error": None}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

# kg.query("MATCH (n) RETURN n")
create_knowledge_graph(linkedin_profile, github_profile, "I want to become a Data Scientist", chat)