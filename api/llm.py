from openai import OpenAI

from os import getenv
import json
import time

from .classes import AnswerModel
from loguru import logger
from .spotify import sp_search
from .system_prompts import natural_language_system_prompt


class LLM:
    def __init__(self, system_prompt, max_tokens=1024, temperature=0):
        self.api_key = getenv("RUNPOD_KEY")
        self.base_url = getenv("LLM_DEPLOY_LINK")
        self.model = getenv("MODEL")

        self.max_tokens = max_tokens
        self.temperature = temperature

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

        self.system_prompt = system_prompt
        self.schema = AnswerModel.model_json_schema()

    def get_system_prompt(self):
        return self.system_prompt

    def constrain_response(self, question):
        prompt_constrained = f"""

        {question}

        Answer using the following JSON schema:
        {self.schema} 

        - If the input is a request for music recommendations:
          - Populate the "results" list with artist, band, or song names.
          - Set "valid_request" to true.
        
        - If the input is NOT a request for music recommendations:
          - Return an empty "results" list.
          - Set "valid_request" to false.

        """

        return prompt_constrained

    def spotify_tool(self, results):
        playlists = [sp_search(res) for res in results]

        final_res = {"suggestion": results, "playlists": playlists}

        return final_res

    def llm_recommendation(self, question):
        messages = [
            {
                "role": "system",
                "content": self.system_prompt,
            }
        ]

        question_constrained = {
            "role": "user",
            "content": self.constrain_response(question),
        }

        messages.append(question_constrained)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            extra_body={"guided_json": self.schema},
        )

        message = response.choices[0].message.content
        if message is None or len(message) == 0:
            raise Exception("LLM response is not valid")

        return json.loads(message)

    def llm_natural_language(self, question, recommendation_response):
        if recommendation_response.get("valid_request"):
            results = recommendation_response["results"]

            tool_response = self.spotify_tool(results)

            final_question = f"""
                You must answer the following question using all the information provided by the tool.

                ### Question:
                {question}

                ### Tool Response:
                {tool_response}

                ### Instructions:
                - Use **every** suggestion from the "suggestion" list in your answer.
                - Mention **every** playlist from the "playlists" list, including the name, link, and cover image.
                - Ensure the answer is in natural language but **includes all the details**.
                - Do not omit or summarize key details.
                - Your response should be engaging and helpful.
            """
        else:
            final_question = "You have to answer: No tools detected. I can't answer."

        final_response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                natural_language_system_prompt,
                {
                    "role": "user",
                    "content": final_question,
                },
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        return final_response.choices[0].message.content

    def llm_pipeline(self, question, max_retries=3, wait_time=5):
        for attempt in range(max_retries):
            try:
                suggestions = self.llm_recommendation(question)
                return self.llm_natural_language(question, suggestions)
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}: API error - {e}")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                else:
                    return "Sorry, I'm having trouble connecting to the server."
