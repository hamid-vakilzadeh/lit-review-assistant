import requests
import streamlit as st


def ai_completion(
        messages: list,
        max_tokens: int = 400,
        temperature: float = 0.3,
        model: str = "anthropic/claude-v1-100k",
        stream: bool = True,
):
    """
    Sends a request to the OpenRouter API to generate a response to the given
    messages.

    :param messages: A list of messages to send to the API.
    :param max_tokens: The maximum number of tokens to generate.
    :param temperature: The temperature to use when generating tokens.
    :param model: The model to use when generating tokens.
    :param stream: Whether to stream the response.
    :return: The response from the API.
    """

    headers = {
        'Accept': 'text/event-stream',  # This is the key to streaming
        'Authorization': 'Bearer ' + st.secrets['OPENROUTER_API_KEY'],
        'HTTP-Referer': st.secrets['OPENROUTER_REFERRER'],
        'X-Title': st.secrets['APP_TITLE'],
    }

    body = {
        'model': model,
        'messages': messages,
        'max_tokens': max_tokens,
        'temperature': temperature,
        'top_p': 1,
        'stream': stream,
    }

    # Show a spinner while the AI is thinking
    with st.spinner(text='AI is thinking...'):
        response = requests.request(
            url="https://openrouter.ai/api/v1/chat/completions",
            method='POST',
            headers=headers,
            json=body,
            stream=stream,
        )

    if response.status_code != 200:
        raise f"""Error: Unable to get response from the server. \n\n {response.status_code, response.text}"""
    else:
        return response
