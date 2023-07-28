import openai
import streamlit as st
from openai.error import InvalidRequestError
import tiktoken
from tenacity import retry, wait_random_exponential, stop_after_attempt

openai.api_key = st.secrets["OPENAI_API_KEY"]


# request gpt chat completion
@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion(
        messages: list,
        model: str = 'gpt-3.5-turbo',
        temperature=0.3,
        top_p=1,
        max_tokens=400,
        stream=False,
        n=1
):
    """
    :param messages: list of messages to send to the OpenAI chatbot
    :param model: the model name to use for the completion
    :param temperature: the temperature to use for the completion
    :param top_p: the top_p to use for the completion
    :param max_tokens: the max_tokens to use for the completion
    :param stream: whether to stream the response or not
    :return: the response from the OpenAI chatbot
    """

    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        stream=stream,
        n=n
    )
    if stream:
        return response

    else:
        if response['choices'][0]['finish_reason'] == 'stop':
            response_ms = response.response_ms
            return dict(answer=response['choices'][0]['message']['content'],
                        completion=response.to_dict(), response_ms=response_ms)
        else:
            raise Exception(f'response incomplete: {response["finish_reason"]}')


def num_tokens_from_messages(
        messages: list,
        model: str = "gpt-3.5-turbo-0301"
):
    """
    Returns the number of tokens used by a list of messages.
    :param messages: list of messages
    :param model: the model name to calculate the number of tokens for
    :return: the number of tokens
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model in ["gpt-3.5-turbo", "gpt-3.5-turbo-16k"]:
        print("Warning: gpt-3.5-turbo may change over time. Returning num tokens assuming gpt-3.5-turbo-0301.")
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301")
    elif model in ["gpt-4", "gpt-4-32k"]:
        print("Warning: gpt-4 may change over time. Returning num tokens assuming gpt-4-0314.")
        return num_tokens_from_messages(messages, model="gpt-4-0314")
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif model == "gpt-4-0314":
        tokens_per_message = 3
        tokens_per_name = 1
    else:
        raise NotImplementedError(f"""num_tokens_from_messages() is not implemented for model {model}. 
        See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


def number_of_tokens_tracker(
        prompt: list
) -> int:
    """
    total number of tokens that will be submitted to OpenAI

    :param prompt: the prompt to be submitted to OpenAI
    :return: the number of tokens
    """
    return num_tokens_from_messages(
                    messages=prompt,
                    model=st.session_state.selected_model
                ) + int(st.session_state.max_words * 4/3)
