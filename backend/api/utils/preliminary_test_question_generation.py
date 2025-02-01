import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_community.graphs import Neo4jGraph

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

kg = Neo4jGraph(
    url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD, database='neo4j'
)

skill_cypher = """MATCH (u:User {name: "Tanmay"})-[r:HAS_SKILL]->(s:Skill)
RETURN s.name"""

goal_cypher = """MATCH (u:User {name: "Tanmay"})-[r:TARGETS]->(s:JobRole)
RETURN s.title;"""

education_cypher = """MATCH (u:User {name: "Tanmay"}) RETURN u.degreeName, u.fieldOfStudy"""

education = kg.query(education_cypher)

skills = kg.query(skill_cypher)

goal_title = kg.query(goal_cypher)

# print(education, skills, goal_title)

API_KEY = os.getenv("GROQ_API_KEY")
chat = ChatGroq(temperature=0, groq_api_key=API_KEY, model_name="deepseek-r1-distill-llama-70b")

# Define individual question schema components
question_schemas = [
    ResponseSchema(name="question_type", description="The Bloom's Taxonomy level and cognitive verb for the question."),
    ResponseSchema(name="skill_tested", description="The specific skill from the user's list or a prerequisite skill being tested."),
    ResponseSchema(name="difficulty_tier", description="The difficulty level of the question: Basic, Intermediate, or Advanced."),
    ResponseSchema(name="question", description="The question statement."),
    ResponseSchema(name="options", description="Four options to choose from, as a list of strings, with distractors reflecting common misconceptions."),
    ResponseSchema(name="right_answer", description="The whole correct answer."),
    ResponseSchema(name="diagnostic_insight", description="What this question reveals about the user's understanding.")
]

questions_schema = StructuredOutputParser.from_response_schemas([ResponseSchema(
    name="questions",
    description="A list of questions, each with a question type, skill tested, difficulty tier, question statement, four options, the correct answer, and diagnostic insight.",
    type="list[dict]"
)])

# Define the parser for a list of questions
format_instructions = questions_schema.get_format_instructions()

text = """I am a {education} student.
I want to become {goal_title} in {goal_duration}.
My current relevant skills are: {skills}.

Please create a personalized 10-question quiz that:
1. Assesses knowledge at all Bloom's Taxonomy levels (Remember, Understand, Apply, Analyze, Evaluate, Create)
2. References my stated skills to build relevant questions
3. Identifies knowledge gaps through targeted distractor options
4. Progresses from foundational to complex concepts
5. Includes this format for each question:

**Question Type**: [Bloom's Level + Cognitive Verb] 
**Skill Tested**: [Specific skill from my list or prerequisite] 
**Difficulty Tier**: [Basic/Intermediate/Advanced based on my education] 
**Question**: [Stem with context] 
**Options**: [Multiple choice/distractors reflecting common misconceptions] 
**Diagnostic Insight**: [What this question reveals about my understanding]

Use the following format for the quiz:
{format_instructions}
"""

prompt_template = PromptTemplate.from_template(text)

def generate_test(education: str, goal_title: str, skills: str) -> dict:
    prompt = prompt_template.invoke({
        "education": str(education),
        "goal_title": str(goal_title),
        "goal_duration": "3 months",
        "skills": str(skills),
        "format_instructions": format_instructions
    })

    response = chat.invoke(prompt)
    test_dict = questions_schema.parse(response.content)

    return (test_dict)

print(generate_test(education, goal_title, skills))

# print(generate_test("Computer Engineering", "Web Development", "I want to learn MERN Stack", "HTML, CSS, JavaScript"))

# # prompt_template.invoke({
# #     "education": "Computer Engineering",
# #     "goal_title": "Web Development",
# #     "goal_desc": "I want to learn MERN Stack",
# #     "skills": "HTML, CSS, JavaScript",
# #     "format_instructions": format_instructions
# # })