from django.contrib import admin

# Register your models here.
# from ChatBotAPI.models import Intent, Pattern, Response, ContextSet
from ChatBotAPI.models import Persona, PersonalityStatement

admin.site.register(Persona)
admin.site.register(PersonalityStatement)

# admin.site.register(Intent)
# admin.site.register(Pattern)
# admin.site.register(Response)
# admin.site.register(ContextSet)