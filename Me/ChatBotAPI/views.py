import json
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

from tensorflow.keras.models import load_model

from ChatBotAPI.utils import constants, misc
from ChatBotAPI.utils.chatbot_serviceV0 import ChatBotServiceV0
from ChatBotAPI.utils.chatbot_service import ChatBotService
# from ChatBotAPI.utils.chatbot_factory import ChatBotFactory
from ChatBotAPI import models

from transformers import OpenAIGPTTokenizer

tokenizer = OpenAIGPTTokenizer.from_pretrained('openai-gpt')
# cbf = ChatBotFactory()

chatbot_model_checkpoint = constants.PATH_TO_MODELS + settings.CHATBOT_MODEL_CHECKPOINT
chatbot_persona = settings.CHATBOT_PERSONA
cbs = ChatBotServiceV0(model_checkpoint=chatbot_model_checkpoint,
                        persona=chatbot_persona)

# Create your views here.
def index(request):
    """index

    Args:
        request (request): api request
    """
    return JsonResponse({"data": "theres nothing at this endpoint"})


def get_chatbot_response(request):
    data = request.GET.get('prompt')
    history = request.GET.get('history')
    answer = cbs.get_response(data, history)
    return JsonResponse({"answer": answer})


def build_chatbot(request):
    # r = cbf.build_chatbot_for_persona(constants.CURRENT_PERSONA) 
    # data = cbf.load_personachat_dataset()
    cbf.train_model_on_dataset()
    return JsonResponse()


def test(request):
    return JsonResponse({"value": "hmmm"})