import os
import logging
from dotenv import load_dotenv
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.chains import LLMChain, SequentialChain
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from api.models import LearningModule, Feedback, Test, Goal, Score

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize models
evaluation_model = ChatGroq(temperature=0, groq_api_key=GROQ_API_KEY, model_name="mixtral-8x7b-32768")
base_model = ChatGroq(temperature=0, groq_api_key=GROQ_API_KEY, model_name="deepseek-r1-distill-llama-70b")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def evaluate(test: Test, feedback: Feedback, score: Score) -> dict:
    """Evaluates the learning progress and provides feedback."""
    goal = Goal.objects.filter(id=test.goal_id.pk).first()
    if not goal:
        raise ValueError("Goal not found.")
    
    evaluation_text = f"""
        I am a {''} student.
        I want to learn {goal.title}, with this description: {goal.description}.
        I have completed the {test.module_info} and given a test on it.
        My score in the test is {score.wrong_fluency} and {score.right_fluency}.
        My feedback regarding the module is {feedback.feedback}.
        Base model is a model which is used to generate the learning module.
        
        {{evaluation_format_instructions}}
    """

    reward_schema = ResponseSchema(name="reward", description="Reward for the base model on a scale of -10 to 10.")
    suggestions_schema = ResponseSchema(name="suggestions", description="Suggestions to improve the base model.")
    evaluation_output_parser = StructuredOutputParser.from_response_schemas([reward_schema, suggestions_schema])
    evaluation_format_instructions = evaluation_output_parser.get_format_instructions()

    evaluation_template = ChatPromptTemplate.from_template(template=evaluation_text)
    evaluation_message = evaluation_template.format_messages(evaluation_format_instructions=evaluation_format_instructions)
    
    try:
        response = evaluation_model.invoke(evaluation_message)
        output_dict = evaluation_output_parser.parse(response.content)
    except Exception as e:
        logger.error(f"Evaluation Model Error: {str(e)}")
        output_dict = {"reward": 0, "suggestions": "Error in evaluation processing."}
    
    return output_dict

def update_learning_module(learning_module: LearningModule, test: Test, feedback: Feedback, score: Score, roadmap: dict, practice: dict) -> tuple:
    """Updates the learning roadmap and practice recommendations based on evaluation."""
    evaluation_results = evaluate(test, feedback, score)
    logger.info(f"Evaluation Results: {evaluation_results}")

    roadmap_schemas = [
        ResponseSchema(name="topics", description="Ordered list of learning topics with time allocation.(Format should be list Data structure in python such that each sentence is at separate index in the list)"),
        ResponseSchema(name="prerequisites", description="Required foundational knowledge.(Format should be list Data structure in python such that each sentence is at separate index in the list)"),
        ResponseSchema(name="weekly_breakdown", description="Detailed weekly learning objectives.(Format should be list Data structure in python such that each sentence is at separate index in the list)"),
        ResponseSchema(name="key_milestones", description="Assessment points and project deadlines.(Format should be list Data structure in python such that each sentence is at separate index in the list)")
    ]
    roadmap_parser = StructuredOutputParser.from_response_schemas(roadmap_schemas)
    roadmap_format = roadmap_parser.get_format_instructions()
    
    roadmap_template = f"""
        This is the feedback for a previous roadmap: {feedback.feedback}. 
        The test scores for the module {test.module_info} are {score.wrong_fluency} and {score.right_fluency}.
        The reward model has given a score of {evaluation_results['reward']}.
        Suggestions: {evaluation_results['suggestions']}.
        Previous roadmap: {roadmap}.
        
        Modify the roadmap accordingly while keeping the existing structure intact.
        
        All text must be in the simple format do not highlight it or make it bold. Do not add end of line or any other non-human readable characters.
        Format: {{format_instructions}}
    """
    roadmap_prompt = PromptTemplate(
        template=roadmap_template,
        input_variables=["feedback", "module_info", "error_fluency", "correct_fluency", "reward", "suggestions", "old_roadmap"],
        partial_variables={"format_instructions": roadmap_format}
    )
    
    practice_schemas = [
        ResponseSchema(name="active_recall", description="Spaced repetition prompts for key concepts.(Format should be list Data structure in python such that each sentence is at separate index in the list)"),
        ResponseSchema(name="hands_on_projects", description="Project ideas with complexity grading.(Format should be list Data structure in python such that each sentence is at separate index in the list)"),
        ResponseSchema(name="debugging_scenarios", description="Common error examples to solve.(Format should be list Data structure in python such that each sentence is at separate index in the list)"),
        ResponseSchema(name="collaborative_learning", description="Pair programming/study group suggestions.(Format should be list Data structure in python such that each sentence is at separate index in the list)")
    ]
    practice_parser = StructuredOutputParser.from_response_schemas(practice_schemas)
    practice_format = practice_parser.get_format_instructions()
    
    practice_template = f"""
        Based on this roadmap: {roadmap},
        create practice instructions that:
        1. Use evidence-based learning techniques
        2. Include multiple difficulty levels
        3. Provide real-world applications
        4. Suggest troubleshooting exercises

        All text must be in the simple format do not highlight it or make it bold. Do not add end of line or any other non-human readable characters.
        
        Format: {{format_instructions}}
    """
    practice_prompt = PromptTemplate(
        template=practice_template,
        input_variables=["roadmap"],
        partial_variables={"format_instructions": practice_format}
    )
    
    roadmap_chain = LLMChain(llm=base_model, prompt=roadmap_prompt, output_key="roadmap")
    practice_chain = LLMChain(llm=base_model, prompt=practice_prompt, output_key="practice")
    
    chain = SequentialChain(
        chains=[roadmap_chain, practice_chain],
        input_variables=["feedback", "module_info", "error_fluency", "correct_fluency", "reward", "suggestions", "old_roadmap"],
        output_variables=["roadmap", "practice"],
        verbose=False
    )
    
    try:
        result = chain({
            "feedback": feedback.feedback,
            "module_info": test.module_info,
            "error_fluency": score.wrong_fluency,
            "correct_fluency": score.right_fluency, 
            "reward": evaluation_results["reward"], 
            "suggestions": evaluation_results["suggestions"], 
            "old_roadmap": roadmap,
        })
    except Exception as e:
        logger.error(f"Chain execution failed: {str(e)}")
        return roadmap, practice
    
    parsed_roadmap = roadmap_parser.parse(result["roadmap"])
    parsed_practice = practice_parser.parse(result["practice"])
    
    # print(roadmap)
    # print(f"Updated Roadmap: {parsed_roadmap}")


    # print(practice)
    # print(f"Updated Practice: {parsed_practice}")
    
    return parsed_roadmap, parsed_practice
