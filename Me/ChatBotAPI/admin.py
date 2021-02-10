from django.contrib import admin

# Register your models here.
# from ChatBotAPI.models import Intent, Pattern, Response, ContextSet
from ChatBotAPI.models import Persona, Statement, History

admin.site.register(Persona)
admin.site.register(Statement)
admin.site.register(History)

# admin.site.register(Intent)
# admin.site.register(Pattern)
# admin.site.register(Response)
# admin.site.register(ContextSet)