import random
import json
import tensorflow as tf
from django.conf import settings
from itertools import chain

from transformers import OpenAIGPTTokenizer, TFOpenAIGPTDoubleHeadsModel
from ChatBotAPI import models

from ChatBotAPI.utils import constants
from ChatBotAPI.utils import misc


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
        persona_statements, history_statements, reply, distractor = self.get_persona(persona)
        
        words, segments, position, sequence = self.build_input(persona_statements, history_statements, reply)
        words_distractor, segments_distractor, _, _ = self.build_input(persona_statements, history_statements, distractor)
        
        words = self.gpt_tokenizer.convert_tokens_to_ids(words)
        segments = self.gpt_tokenizer.convert_tokens_to_ids(segments)
        words_distractor = self.gpt_tokenizer.convert_tokens_to_ids(words_distractor)
        segments_distractor = self.gpt_tokenizer.convert_tokens_to_ids(segments_distractor)
        
        # Prepare our language modeling targets: keep only the reply segment, -1 on the rest
        lm_targets = ([-1] * sum(len(s) for s in sequence[:-1])) \
                    + [-1] + self.gpt_tokenizer.convert_tokens_to_ids(sequence[-1][1:])
        lm_distractor = [-1] * len(words_distractor)

        # Store the position of the last tokens for the next-sentence prediction loss
        last_token = len(words) - 1
        last_token_distractor = len(words_distractor) - 1

        # Now we can pad reply and distractor inputs and targets to the same length
        padding_length = max(len(words), len(words_distractor))
        def pad(x, padding):
            return x + [padding] * (padding_length - len(x))

        (words, words_distractor,
        segments, segments_distractor) = [pad(x, self.gpt_tokenizer.convert_tokens_to_ids('<pad>'))
                                        for x in (words, words_distractor,
                                                    segments, segments_distractor)]

        (lm_targets, lm_distractor) = [pad(x, -1) for x in (lm_targets, lm_distractor)]

        input_ids = tf.convert_to_tensor([[words, words_distractor]], dtype=tf.float32)
        token_type_ids = tf.convert_to_tensor([[segments, segments_distractor]], dtype=tf.float32)
        mc_token_ids = tf.convert_to_tensor([[last_token, last_token_distractor]], dtype=tf.float32)
        lm_labels = tf.convert_to_tensor([[lm_targets, lm_distractor]], dtype=tf.float32)
        mc_labels = tf.convert_to_tensor([0], dtype=tf.float32)

        # r = {
        #     "input_ids": str(input_ids),
        #     "mc_token_ids": str(mc_token_ids),
        #     "lm_labels": str(lm_labels),
        #     "mc_labels": str(mc_labels),
        #     "token_type_ids": str(token_type_ids)
        # }

        


    def build_input(self, persona_statements, history_statements, reply):
        sequence = [[self.bos] + list(chain(*persona_statements))] + history_statements + [reply + [self.eos]]
        sequence = [sequence[0]] + [ [self.speaker2 if (len(sequence)-i) % 2 else self.speaker1] + s
                                    for i, s in enumerate(sequence[1:])]
        # Build our word, segments and position inputs from the sequence
        words = list(chain(*sequence))                          # word tokens
        segments = [self.speaker2 if i % 2 else self.speaker1   # segment tokens
                    for i, s in enumerate(sequence) for _ in s]
        position = list(range(len(words)))                      # position tokens
        return words, segments, position, sequence


    def get_persona(self, persona):
        persona = models.Persona.objects.get(name=persona)
        if not persona:
            return "persona could not be found"
        persona_statements = [s.format_to_tokens(self.gpt_tokenizer) for s in persona.statements.all()]
        history_statements = [h.format_to_tokens(self.gpt_tokenizer) for h in persona.history.order_by('-previous')]
        other = models.History.objects.all().exclude(Persona=persona)
        distractor = random.choice(other).format_to_tokens(self.gpt_tokenizer)
        reply = history_statements.pop()
        history_statements.reverse()
        return persona_statements, history_statements, reply, distractor

    def load_personachat_dataset(self):
        with open(constants.PERSONACHAT_DATASET_PATH,"r", encoding="utf-8") as f:
            data = json.loads(f.read())
            data = misc.modify_nested_dict(data, self.format_data_string)
            return data

    def format_data_string(self, string):
        tokenized_string = self.gpt_tokenizer.tokenize(string)
        ids = self.gpt_tokenizer.convert_tokens_to_ids(tokenized_string)
        return ids


    def make_prediction(self, words):
        result = self.gpt_model.predict(words)
        #last = result.logits[0, -1, :]
        softmax_val = tf.argmax(tf.squeeze(result.logits), axis=1) 
        string = self.gpt_tokenizer.decode(softmax_val)

        return string


