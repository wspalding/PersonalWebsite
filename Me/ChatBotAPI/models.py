from django.db import models


class Persona(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
            return self.name

class PersonalityStatement(models.Model):
    statement = models.CharField(max_length=100)
    Persona = models.ForeignKey('ChatBotAPI.Persona', on_delete=models.CASCADE)

    def __str__(self):
        return self.statement


        
# # Create your models here.
# class Intent(models.Model):
#     tag = models.CharField(max_length=50)
#     # context_set = models.CharField(max_length=100)

#     def __str__(self):
#         return self.tag

#     def patters(self):
#         return self.Pattern_set.all()


# class Pattern(models.Model):
#     value = models.CharField(max_length=100)
#     Intent = models.ForeignKey("ChatBotAPI.Intent", on_delete=models.CASCADE)

#     def __str__(self):
#         return self.value
    

# class Response(models.Model):
#     message = models.CharField(max_length=100)
#     Intent = models.ForeignKey("ChatBotAPI.Intent", on_delete=models.CASCADE)

#     def __str__(self):
#         return self.message
    

# class ContextSet(models.Model):
#     value = models.CharField(max_length=100)
#     Intent = models.ForeignKey("ChatBotAPI.Intent", on_delete=models.CASCADE)

#     def __str__(self):
#         return self.value
    
# class Word(models.Model):
#     value = models.CharField(max_length=100)

#     def __str__(self):
#         return self.value