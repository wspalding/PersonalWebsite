from django.conf import settings
from itertools import chain

from transformers import OpenAIGPTTokenizer, TFOpenAIGPTDoubleHeadsModel
from ChatBotAPI import models

from ChatBotAPI.utils import constants


class ChatBotFactory():
    def __init__(self):
        self.gpt_model = TFOpenAIGPTDoubleHeadsModel.from_pretrained('openai-gpt')
        self.gpt_tokenizer = OpenAIGPTTokenizer.from_pretrained('openai-gpt')
        self.bos, self.eos, self.speaker1, self.speaker2, self.pad = constants.SPECIAL_TOKENS

        orig_num_tokens = len(self.gpt_tokenizer.encoder)
        num_added_tokens = self.gpt_tokenizer.add_special_tokens(constants.ATTR_TO_SPECIAL_TOKEN)
        if num_added_tokens > 0:
            self.gpt_model.resize_token_embeddings(new_num_tokens=orig_num_tokens + num_added_tokens)
        # self.gpt_model.set_num_special_tokens(len(constants.SPECIAL_TOKENS))


    def build_chatbot_for_persona(self, persona):
        words, segments, position, sequence = self.build_input(persona)

        words = self.gpt_tokenizer.convert_tokens_to_ids(words)
        segments = self.gpt_tokenizer.convert_tokens_to_ids(segments)
        return words, segments

    def build_input(self, persona):
        persona = models.Persona.objects.get(name=persona)
        if not persona:
            return "persona could not be found"
        persona_statements = [s.format_to_tokens(self.gpt_tokenizer) for s in persona.statements.all()]
        history_statements = [h.format_to_tokens(self.gpt_tokenizer) for h in persona.history.order_by('-previous')]
        reply = history_statements.pop()
        history_statements.reverse()

        sequence = [[self.bos] + list(chain(*persona_statements))] + history_statements + [reply + [self.eos]]
        sequence = [sequence[0]] + [ [self.speaker2 if (len(sequence)-i) % 2 else self.speaker1] + s
                                    for i, s in enumerate(sequence[1:])]
        # Build our word, segments and position inputs from the sequence
        words = list(chain(*sequence))                          # word tokens
        segments = [self.speaker2 if i % 2 else self.speaker1   # segment tokens
                    for i, s in enumerate(sequence) for _ in s]
        position = list(range(len(words)))                      # position tokens
        return words, segments, position, sequence

        # return persona_statements, history_statements, reply
