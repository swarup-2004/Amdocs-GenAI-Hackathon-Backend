from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain, SequentialChain
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain.output_parsers import ResponseSchema, StructuredOutputParser

API_KEY = os.getenv("GROQ_API_KEY")
chat = ChatGroq(temperature=0, groq_api_key=API_KEY, model_name="deepseek-r1-distill-llama-70b")

# =====================
# 1. Roadmap Components
# =====================
roadmap_schemas = [
    ResponseSchema(name="topics", description="Ordered list of learning topics with time allocation(Format should be list Data structure in python such that each sentence is at separate index in the list)"),
    ResponseSchema(name="prerequisites", description="Required foundational knowledge(Format should be list Data structure in python such that each sentence is at separate index in the list)"),
    ResponseSchema(name="weekly_breakdown", description="Detailed weekly learning objectives(Format should be list Data structure in python such that each sentence is at separate index in the list)"),
    ResponseSchema(name="key_milestones", description="Assessment points and project deadlines(Format should be list Data structure in python such that each sentence is at separate index in the list)")
]
roadmap_parser = StructuredOutputParser.from_response_schemas(roadmap_schemas)
roadmap_format = roadmap_parser.get_format_instructions()

roadmap_template = """As a {education} student with {skills}, I have {time_period} to learn {goal_title}: {goal_desc}.

Create a comprehensive learning roadmap that:
1. Addresses my current skill level
2. Includes practical projects
3. Balances theory/practice
4. Has clear progression markers


All text must be in the simple format do not highlight it or make it bold. Do not add end of line or any other non-human readable characters.

Format: {format_instructions}"""

roadmap_prompt = PromptTemplate(
    template=roadmap_template,
    input_variables=["education", "skills", "time_period", "goal_title", "goal_desc"],
    partial_variables={"format_instructions": roadmap_format}
)

# ========================
# 2. Practice Components
# ========================
practice_schemas = [
    ResponseSchema(name="active_recall", description="Spaced repetition prompts for key concepts(Format should be list Data structure in python such that each sentence is at separate index in the list)"),
    ResponseSchema(name="hands_on_projects", description="Project ideas with complexity grading(Format should be list Data structure in python such that each sentence is at separate index in the list))"),
    ResponseSchema(name="debugging_scenarios", description="Common error examples to solve(Format should be list Data structure in python such that each sentence is at separate index in the list)"),
    ResponseSchema(name="collaborative_learning", description="Pair programming/study group suggestions(Format should be list Data structure in python such that each sentence is at separate index in the list)")
]
practice_parser = StructuredOutputParser.from_response_schemas(practice_schemas)
practice_format = practice_parser.get_format_instructions()

practice_template = """Based on this roadmap: {roadmap}

Create practice instructions that:
1. Use evidence-based learning techniques
2. Include multiple difficulty levels
3. Provide real-world applications
4. Suggest troubleshooting exercises

All text must be in the simple format do not highlight it or make it bold. Do not add end of line or any other non-human readable characters.

Format: {format_instructions}"""

practice_prompt = PromptTemplate(
    template=practice_template,
    input_variables=["roadmap"],
    partial_variables={"format_instructions": practice_format}
)

# =====================
# 3. Quiz Components
# =====================
# (Using the existing quiz schema from question)

# question_schemas = [
#     ResponseSchema(name="question_type", description="The Bloom's Taxonomy level and cognitive verb for the question."),
#     ResponseSchema(name="skill_tested", description="The specific skill from the user's list or a prerequisite skill being tested."),
#     ResponseSchema(name="difficulty_tier", description="The difficulty level of the question: Basic, Intermediate, or Advanced."),
#     ResponseSchema(name="question", description="The question statement."),
#     ResponseSchema(name="options", description="Four options to choose from, as a list of strings, with distractors reflecting common misconceptions."),
#     ResponseSchema(name="right_answer", description="The whole correct answer."),
#     ResponseSchema(name="diagnostic_insight", description="What this question reveals about the user's understanding.")
# ]

# quiz_parser = StructuredOutputParser.from_response_schemas([ResponseSchema(
#     name="questions",
#     description="A list of questions, each with a question type, skill tested, difficulty tier, question statement, four options, the correct answer, and diagnostic insight.",
#     type="list[dict]"
# )])
# quiz_format = quiz_parser.get_format_instructions()

# quiz_template = """Given this roadmap: {roadmap}
# And these practice activities: {practice}

# Generate a diagnostic quiz with 10 questions that:
# 1. Assesses knowledge at all Bloom's Taxonomy levels (Remember, Understand, Apply, Analyze, Evaluate, Create)
# 2. Covers all roadmap stages and creates relevant questions
# 3. Mirrors real practice challenges
# 4. Progresses from recognition to creation
# 5. Includes performance analysis hooks

# **Question Type**: [Bloom's Level + Cognitive Verb]
# **Skill Tested**: [Specific skill from my roadmap]
# **Difficulty Tier**: [Basic/Intermediate/Advanced based on my roadmap]
# **Question**: [Stem with context]
# **Options**: [Multiple choice/distractors reflecting common misconceptions]
# **Diagnostic Insight**: [What this question reveals about my understanding and what I have learnt]

# Format: {format_instructions}"""

# quiz_prompt = PromptTemplate(
#     template=quiz_template,
#     input_variables=["roadmap", "practice"],
#     partial_variables={"format_instructions": quiz_format}
# )

# ======================
# Chained Execution
# ======================
def create_learning_cell_chain(llm):
    roadmap_chain = LLMChain(
        llm=llm,
        prompt=roadmap_prompt,
        output_key="roadmap"
    )
    
    practice_chain = LLMChain(
        llm=llm,
        prompt=practice_prompt,
        output_key="practice"
    )
    
    # quiz_chain = LLMChain(
    #     llm=llm,
    #     prompt=quiz_prompt,
    #     output_key="quiz"
    # )

    return SequentialChain(
        chains=[roadmap_chain, practice_chain],
        input_variables=["education", "skills", "time_period", "goal_title", "goal_desc"],
        output_variables=["roadmap", "practice"],
        verbose=True
    )

# ======================
# Usage Example
# ======================

chain = create_learning_cell_chain(chat)
    
def call_chain(education, skills, time_period, goal_title, goal_desc):

    result = chain({
        "education": education,
        "skills": skills,
        "time_period": time_period,
        "goal_title": goal_title,
        "goal_desc": goal_desc
    })

    parsed_roadmap = roadmap_parser.parse(result["roadmap"])
    parsed_practice = practice_parser.parse(result["practice"])

    return parsed_roadmap, parsed_practice

# parsed_roadmap, parsed_practice, parsed_quiz = call_chain()

# print("🚀 Learning Roadmap:")
# print(parsed_roadmap)
        
# print("\n🔧 Practice Instructions:")
# print(parsed_practice)
        
# print("\n📝 Assessment Quiz:")
# print(parsed_quiz)