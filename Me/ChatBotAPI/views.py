from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

from ChatBotAPI.utils.train import build_words_and_classes

# Create your views here.
def index(request):
    """index

    Args:
        request (request): api request
    """
    return JsonResponse({"data": "theres nothing at this endpoint"})


def get_chatbot_response(request):
    question = request.GET.get("prompt")
    return JsonResponse({"answer": question})


def build_chatbot(request):
    build_words_and_classes()
    return JsonResponse({"success": True})
