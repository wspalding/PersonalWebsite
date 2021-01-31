from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    """
    home page

    Returns:
        HttpResponse: index page html
    """
    return render(request, 'index.html')



def get_chatbot_response(request):
    """
    API
    
        gets a response from the chatbot given a string

    Args:
        request (string): input to the chatbot
    Returns:
        string: output from chatbot
    """
    pass


def subscribe(request):
    """
    API
    
        adds user enail to subscriber email list

    Args:
        request (string): users email
    Returns:
        string: confirmation is successful
    """
    pass