from functools import cache
import os
from openai import OpenAI
from dotenv import load_dotenv

def get_openai_client():
    load_dotenv()
    api_key = os.getenv("API_KEY")
    return OpenAI(api_key=api_key)

oai_client = get_openai_client()

@cache
def call_llm(system_prompt: str, user_prompt: str, only_content: bool = True, **kwargs):
    response = oai_client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        **kwargs
    )
    if only_content:
        return response.choices[0].message.content
    else:
        return response

@cache
def gpt_translate(text: str, source_language: str, target_language: str = 'english', **kwargs):
    if "model" not in kwargs:
        kwargs["model"] = "gpt-5-mini"
        kwargs["reasoning_effort"] = "minimal"
    system_prompt = f"You are a helpful translator working on customer support emails. You are translating emails from {source_language} (or other languages) to {target_language}. Don't write any other text than the translation."
    user_prompt = text
    return call_llm(system_prompt, user_prompt, **kwargs)

