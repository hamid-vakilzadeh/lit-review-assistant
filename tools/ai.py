import requests
import streamlit as st


def ai_completion(
        messages: list,
        max_tokens: int = 400,
        temperature: float = 0.3,
        model: str = "anthropic/claude-v1-100k",
        stream: bool = True,

):
    headers = {
        'Accept': 'text/event-stream',
        'Authorization': 'Bearer ' + st.secrets['OPENROUTER_API_KEY'],
        'HTTP-Referer': st.secrets['OPENROUTER_REFERRER'],
        'X-Title': st.secrets['APP_TITLE'],
    }

    body = {
        'model': model,  # Optional (user controls the default)
        'messages': messages,
        'max_tokens': max_tokens,
        'temperature': temperature,
        'top_p': 1,
        'stream': stream,  # Optional (user controls the default)
    }

    with st.spinner(text='AI is thinking...'):
        response = requests.request(
            url="https://openrouter.ai/api/v1/chat/completions",
            method='POST',
            headers=headers,
            json=body,
            stream=stream,
        )

    if response.status_code != 200:
        raise "Error: Unable to get response from the server."
    elif stream:
        return response


prompt = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"}
        ]

"""
response = ai_completion(
    messages=prompt,
    model="google/palm-2-chat-bison",
    stream=True,
    temperature=0.7,
    max_tokens=400,
)
import json
collected_chunks = []
report = []
for line in response.iter_lines():
    if line and 'data' in line.decode('utf-8'):
        content = line.decode('utf-8').replace('data: ', '')
        if 'content' in content:
            message = json.loads(content, strict=False)
            collected_chunks.append(message)  # save the event response
            report.append(message['choices'][0]['delta']['content'])
            last_response = "".join(report).strip()
            print(f'{last_response}')
"""