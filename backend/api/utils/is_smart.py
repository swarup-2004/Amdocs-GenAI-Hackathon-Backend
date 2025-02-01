from dotenv import load_dotenv
import os
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
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

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
chat = ChatGroq(temperature=0, groq_api_key=GROQ_API_KEY, model_name="deepseek-r1-distill-llama-70b")

def is_smart_goal(goal_title: str, skills: str) -> dict:
    
    is_smart_goal_template = """
    I am studnet and I want to become {goal_title}.
    I have the following skills: {skills} and the duration for this goal is {goal_duration} days .is this achievable goal?
    {smart_format_instructions}
    """

    # Schmea for the output
    is_smart_schmea = ResponseSchema(name="is_smart", description="whether the goal is smart or not")
    reason_schema = ResponseSchema(name="reason", description="reason for the answer")

    # Output parser
    is_smart_output_parse = StructuredOutputParser.from_response_schemas([is_smart_schmea, reason_schema])
    smart_format_instructions = is_smart_output_parse.get_format_instructions()

    # Prompt 
    smart_prompt = ChatPromptTemplate.from_template(template=is_smart_goal_template)

    print(smart_prompt)
    is_smart_message = smart_prompt.format_messages(
        goal_title=str(goal_title),
        skills=str(skills),
        goal_duration="10 years",
        smart_format_instructions=smart_format_instructions
    )

    response = chat.invoke(is_smart_message)

    is_smart_dict = is_smart_output_parse.parse(response.content)

    return is_smart_dict

print(is_smart_goal(goal_title, skills))
