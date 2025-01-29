from django.shortcuts import render
from langchain_groq import ChatGroq
from langchain.chains import ConversationChain
from langchain.memory import ConversationSummaryBufferMemory
from rest_framework.views import APIView
from rest_framework.response import Response
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize the LLM
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
llm = ChatGroq(temperature=0, groq_api_key=GROQ_API_KEY, model_name="llama3-8b-8192")

# Initialize Conversation Memory to maintain context across requests
memory = ConversationSummaryBufferMemory(llm=llm, max_token_limit=300)
conversation = ConversationChain(llm=llm, memory=memory)


class ChatBotAPIView(APIView):
    def get(self, request):
        message = request.data.get("message", "")
        is_start = request.data.get("is_start", False)

        print(is_start)

        if is_start:
            goal_title = request.data.get("goal_title", "a new skill")
            goal_desc = request.data.get("goal_description", "No description provided.")

            input_message = (
                f"I am a student and I want to learn {goal_title}. "
                f"The description for this skill is: {goal_desc}. "
                "Please solve my doubts regarding the same."
            )
            
            # Save initial context
            memory.save_context(
                {"input": input_message},
                {"output": "I am happy to help you. Please ask your doubts."}
            )
            response = conversation.invoke(input_message)
        
        else:
            response = conversation.invoke(message)

        print(response)

        return Response(response)
