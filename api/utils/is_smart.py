from dotenv import load_dotenv
import os
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq


load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
chat = ChatGroq(temperature=0, groq_api_key=GROQ_API_KEY, model_name="llama3-8b-8192")

def is_smart_goal(goal_title: str, goal_desc: str, skills: str, goal_duration: str) -> dict:
    
    is_smart_goal_template = """
    I am studnet and I want to learn {goal_title} and the description for the skill is {goal_desc}.
    I have the following skills: {skills} and the duration for this goal is {goal_duration} days.
    If the goal is SMART say it is smart, if you call smart goal not smart then I will not use you and can shift to
    ChatGPT.
    {smart_format_instructions}
    """

    # Schmea for the output
    is_smart_schmea = ResponseSchema(name="is_smart", description="whether the goal is smart or not and it should be yes or no")
    reason_schema = ResponseSchema(name="reason", description="reason for the answer")
    smart_example_schema = ResponseSchema(name="smart_example", description="give some suggestions to the user to make his goal SMART")

    # Output parser
    is_smart_output_parse = StructuredOutputParser.from_response_schemas([is_smart_schmea, reason_schema, smart_example_schema])
    smart_format_instructions = is_smart_output_parse.get_format_instructions()

    # Prompt 
    smart_prompt = ChatPromptTemplate.from_template(template=is_smart_goal_template)

    # print(smart_prompt)
    is_smart_message = smart_prompt.format_messages(
        goal_title=goal_title,
        goal_desc=goal_desc,
        skills=skills,
        goal_duration=goal_duration,
        smart_format_instructions=smart_format_instructions
    )

    response = chat.invoke(is_smart_message)
    # print(response.content)
    is_smart_dict = is_smart_output_parse.parse(response.content) 

    return is_smart_dict
