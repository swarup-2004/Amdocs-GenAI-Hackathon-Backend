from dotenv import load_dotenv
import os
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq


load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
chat = ChatGroq(temperature=0, groq_api_key=GROQ_API_KEY, model_name="deepseek-r1-distill-llama-70b")

def analyze_learning_goal(goal_title: str, goal_desc: str, skills: list, goal_duration: str) -> dict:
    analysis_template = """
    Analyze the following learning goal and provide a comprehensive assessment:
    
    Goal Title: {goal_title}
    Description: {goal_desc}
    Current Skills: {skills}
    Target Duration: {goal_duration} days
    
    Perform the following analysis:
    1. SMART Goal Evaluation (Specific, Measurable, Achievable, Relevant, Time-bound)
    2. Bloom's Taxonomy Level Determination (Choose from: Remember, Understand, Apply, Analyze, Evaluate, Create)
    3. Skill Gap Analysis (Missing skills required for this goal)
    4. Recommended Learning Resources
    5. Suggested Milestones with Timeline
    
    {format_instructions}
    
    Additional Considerations:
    - Consider industry standards for skill progression
    - Account for the stated time frame in recommendations
    - Suggest practical projects for skill application
    - Identify potential mentorship opportunities
    """
    
    # Response schemas
    response_schemas = [
        ResponseSchema(name="is_smart", description="Whether the goal meets SMART criteria (True/False)"),
        ResponseSchema(name="smart_evaluation", description="Detailed SMART analysis with component ratings"),
        ResponseSchema(name="blooms_level", description="Primary Bloom's Taxonomy level required for this goal"),
        ResponseSchema(name="skill_gaps", description="List of missing skills required to achieve this goal"),
        ResponseSchema(name="learning_resources", description="Recommended resources to bridge skill gaps"),
        ResponseSchema(name="milestones", description="Suggested timeline with key milestones"),
        ResponseSchema(name="assessment_strategy", description="Recommended assessment methods for this goal"),
        ResponseSchema(name="risk_factors", description="Potential obstacles and mitigation strategies")
    ]

    # Output parser
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()

    # Create prompt
    prompt = ChatPromptTemplate.from_template(template=analysis_template)
    
    # Generate response
    message = prompt.format_messages(
        goal_title=goal_title,
        goal_desc=goal_desc,
        skills=", ".join(skills),
        goal_duration=goal_duration,
        format_instructions=format_instructions
    )
    
    response = chat.invoke(message)
    return output_parser.parse(response.content)

# def is_smart_goal(goal_title: str, goal_desc: str, skills: str, goal_duration: str) -> dict:
    
#     is_smart_goal_template = """
#     I am studnet and I want to learn {goal_title} and the description for the skill is {goal_desc}.
#     I have the following skills: {skills} and the duration for this goal is {goal_duration} days .is this a smart goal?
#     {smart_format_instructions}
#     """

#     # Schmea for the output
#     is_smart_schmea = ResponseSchema(name="is_smart", description="whether the goal is smart or not")
#     reason_schema = ResponseSchema(name="reason", description="reason for the answer")

#     # Output parser
#     is_smart_output_parse = StructuredOutputParser.from_response_schemas([is_smart_schmea, reason_schema])
#     smart_format_instructions = is_smart_output_parse.get_format_instructions()

#     # Prompt 
#     smart_prompt = ChatPromptTemplate.from_template(template=is_smart_goal_template)

#     print(smart_prompt)
#     is_smart_message = smart_prompt.format_messages(
#         goal_title=goal_title,
#         goal_desc=goal_desc,
#         skills=skills,
#         goal_duration=goal_duration,
#         smart_format_instructions=smart_format_instructions
#     )

#     response = chat.invoke(is_smart_message)

#     is_smart_dict = is_smart_output_parse.parse(response.content)

#     return is_smart_dict
# print(analyze_learning_goal("python", "learn python", ["python"], "30"))
# print("////////////////////////////////////////////////////////////////////////////////////////")
# print(is_smart_goal("python", "learn python", "python", "30"))