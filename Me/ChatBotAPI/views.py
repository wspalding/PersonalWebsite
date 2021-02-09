import json
import random
import pickle
# import nltk

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse


from ChatBotAPI.utils.train import create_model
from tensorflow.keras.models import load_model

from ChatBotAPI.utils import constants
from ChatBotAPI.utils.train import lemmatizer

from ChatBotAPI.utils.chatbot_service import ChatBotService

# chatbot = ChatBotService(constants.PATH_TO_UTILS + constants.CHATBOT_MODEL_FILE)

# Create your views here.
def index(request):
    """index

    Args:
        request (request): api request
    """
    return JsonResponse({"data": "theres nothing at this endpoint"})


def get_chatbot_response(request):
    data = json.loads(request.body)
    question = data.get("prompt")
    answer = chatbot.getResponse(question)
    return JsonResponse({"answer": answer})


def build_chatbot(request):
    create_model()
    return JsonResponse({"success": True})


def test(request):
    return JsonResponse({"value": t.value})