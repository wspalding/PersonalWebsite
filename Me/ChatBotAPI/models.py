from django.db import models


class Persona(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
            return self.name

class Statement(models.Model):
    statement = models.CharField(max_length=100)
    Persona = models.ForeignKey('ChatBotAPI.Persona', 
                                    on_delete=models.CASCADE,
                                    related_name='statements')

    def __str__(self):
        return self.statement

    def format_to_tokens(self, tokenizer):
        return tokenizer.tokenize(self.statement)

class History(models.Model):
    phrase = models.CharField(max_length=100)
    pervious = models.ForeignKey("ChatBotAPI.History", 
                                    on_delete=models.SET_NULL,
                                    related_name='previous',
                                    null=True,
                                    blank=True)
    Persona = models.ForeignKey('ChatBotAPI.Persona', 
                                    on_delete=models.CASCADE,
                                    related_name='history')

    def __str__(self):
        return self.phrase

    def format_to_tokens(self, tokenizer):
        return tokenizer.tokenize(self.phrase)

