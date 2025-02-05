from dotenv import load_dotenv
import os
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq


load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
chat = ChatGroq(temperature=0, groq_api_key=GROQ_API_KEY, model_name="mixtral-8x7b-32768")

def recommend_course(goal_title: str, goal_desc: str) -> dict:
    course_title_schema = ResponseSchema(name="course_title", description="The title of the recommended course.")
    course_url_schema = ResponseSchema(name="course_url", description="The URL of the recommended course.")
    course_provider_schema = ResponseSchema(name="course_provider", description="The provider of the recommended course.")
    
    output_parser = StructuredOutputParser.from_response_schemas([course_title_schema, course_url_schema, course_provider_schema])
    recommend_format_instructions = output_parser.get_format_instructions()

    

    course_list_schema = ResponseSchema(name="course_list", description=f"python list of the schema in the {recommend_format_instructions} ")
    course_list_parser = StructuredOutputParser.from_response_schemas([course_list_schema])
    recommend_format_instructions = course_list_parser.get_format_instructions()

    text = """
        I am a student and I want to learn {goal_title}. The description for this skill is: {goal_desc}.
        Please recommend a course for me in the **exact JSON format** below, without any additional text:
        Suggest python list of 5 courses in the below format and also sort the courses according to the rating.
        Some courses from udemy and some from the coursera
        {recommend_format_instructions}
    """

    recommend_course_template = ChatPromptTemplate.from_template(text)
    recommend_message = recommend_course_template.format_messages(goal_title=goal_title, goal_desc=goal_desc, recommend_format_instructions=recommend_format_instructions)

    response = chat.invoke(recommend_message)

    # return response.content

    try:
        output_dict = course_list_parser.parse(response.content)
    except KeyError as e:
        print("Parsing error: ", e)
        print("Raw Response:", response.content)
        return {}

    return output_dict