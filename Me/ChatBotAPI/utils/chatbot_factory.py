from django.conf import settings
from itertools import chain

from transformers import OpenAIGPTTokenizer, TFOpenAIGPTDoubleHeadsModel
from ChatBotAPI import models

from ChatBotAPI.utils import constants


class ChatBotFactory():
    def __init__(self):
        self.gpt_model = TFOpenAIGPTDoubleHeadsModel.from_pretrained('openai-gpt')
        self.gpt_tokenizer = OpenAIGPTTokenizer.from_pretrained('openai-gpt')

        orig_num_tokens = len(self.gpt_tokenizer.encoder)
        num_added_tokens = self.gpt_tokenizer.add_special_tokens(constants.ATTR_TO_SPECIAL_TOKEN)
        if num_added_tokens > 0:
            self.gpt_model.resize_token_embeddings(new_num_tokens=orig_num_tokens + num_added_tokens)
        # self.gpt_model.set_num_special_tokens(len(constants.SPECIAL_TOKENS))


    def build_chatbot_for_persona(self, persona):
        bos, eos, speaker1, speaker2, pad = constants.SPECIAL_CHARACTERS

        persona_statements, history_statements, reply = self.build_input


    def build_input(self):
        persona = models.Persona.objects.get(name=constants.CURRENT_PERSONA)
        persona_statements = [s.format_to_tokens(self.gpt_tokenizer) for s in persona.statements.all()]
        history_statements = [h.format_to_tokens(self.gpt_tokenizer) for h in persona.history.order_by('previous')]
        reply = history_statements.pop()
        return persona_statements, history_statements, reply
