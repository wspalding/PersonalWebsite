from ollama import chat
from ollama import ChatResponse
from json import JSONEncoder


def getResponse(system_prompt, question, model_type, think=True):
    response: ChatResponse = chat(model=str(model_type), messages=[
        {
            'role': 'system',
            'content': str(system_prompt),
        },
        {
            'role': 'user',
            'content': str(question),
        },
        ], think=think)
    print('message:', response.message, '\n')
    return response.message.content


def getChatResponse(message_text):
    return getResponse(
        'You are a helpful AI assistant whos job is to chat with people who visit William Spalding\'s website and hype him up.',
        message_text,
        'deepseek-r1:8b'
        )