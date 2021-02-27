import random
import json
from collections import defaultdict
import tensorflow as tf
import numpy as np
from django.conf import settings
from itertools import chain
from tensorflow.python.ops.math_ops import argmax

from transformers import OpenAIGPTTokenizer, TFOpenAIGPTDoubleHeadsModel
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import CategoricalCrossentropy
from ChatBotAPI import models

from ChatBotAPI.utils import constants
from ChatBotAPI.utils import misc


class ChatBotFactory():
    def __init__(self, **kwargs):
        self.gpt_model = TFOpenAIGPTDoubleHeadsModel.from_pretrained('openai-gpt')
        self.gpt_tokenizer = OpenAIGPTTokenizer.from_pretrained('openai-gpt')
        self.bos, self.eos, self.speaker1, self.speaker2, self.pad = constants.SPECIAL_TOKENS
        orig_num_tokens = len(self.gpt_tokenizer.encoder)
        num_added_tokens = self.gpt_tokenizer.add_special_tokens(constants.ATTR_TO_SPECIAL_TOKEN)
        if num_added_tokens > 0:
            self.gpt_model.resize_token_embeddings(new_num_tokens=orig_num_tokens + num_added_tokens)
        
        self.bos_id = self.gpt_tokenizer.convert_tokens_to_ids(self.bos)
        self.eos_id = self.gpt_tokenizer.convert_tokens_to_ids(self.eos)
        self.speaker1_id = self.gpt_tokenizer.convert_tokens_to_ids(self.speaker1)
        self.speaker2_id = self.gpt_tokenizer.convert_tokens_to_ids(self.speaker2)
        self.pad_id = self.gpt_tokenizer.convert_tokens_to_ids(self.pad)

        # data vars
        self.num_candidates = kwargs.get('num_candidates', 2)
        self.personality_permutations = kwargs.get('personality_permutations', 1)
        self.max_history = kwargs.get('max_history', 2)

        # training vars
        self.training_epocs = kwargs.get('training_epochs', 3)
        self.training_batch_size = kwargs.get('training_batch_size', 4)
        self.learning_rate = kwargs.get('lr', 6.25e-5)

        #compile model
        self.build_model()


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

        
    def load_personachat_dataset(self, formatted=True):
        if formatted:
            file = constants.PERSONACHAT_FORMATTED_DATASET_PATH
        else:
            file = constants.PERSONACHAT_DATASET_PATH
        with open(file,"r", encoding="utf-8") as f:
            data = json.loads(f.read())
            return data

    def train_model_on_dataset(self):
        # data = self.load_personachat_dataset()
        # data['train'] = self.format_dataset(data['train'])
        # data['valid'] = self.format_dataset(data['valid'])
        print(self.gpt_model.summary())
        
        train, valid = self.get_formatted_dataset(self.load_personachat_dataset)
        input_ids, mc_token_ids, lm_labels, mc_labels, token_type_ids = train
        self.gpt_model.fit(x=[input_ids, mc_token_ids, token_type_ids],
                            y=[lm_labels, mc_labels], 
                            epochs=self.training_epocs, 
                            batch_size=self.training_batch_size)
        pass

    def build_model(self):
        
        optimizer = Adam(learning_rate=self.learning_rate)
        loss = CategoricalCrossentropy()

        self.gpt_model.compile(optimizer=optimizer, 
                                loss=loss, 
                                metrics=[])

    def save_model(self, file_name):
        pass

    def get_formatted_dataset(self, data_function):
        personachat = data_function()

        datasets = {"train": defaultdict(list), "valid": defaultdict(list)}
        for dataset_name, dataset in personachat.items():
            num_candidates = len(dataset[0]["utterances"][0]["candidates"])
            if self.num_candidates > 0 and dataset_name == 'train':
                num_candidates = min(self.num_candidates, num_candidates)
            for dialog in dataset:
                persona = dialog["personality"].copy()
                for _ in range(self.personality_permutations):
                    for utterance in dialog["utterances"]:
                        history = utterance["history"][-(2*self.max_history+1):]
                        for j, candidate in enumerate(utterance["candidates"][-num_candidates:]):
                            lm_labels = bool(j == num_candidates-1)
                            instance = self.build_input(persona, history, candidate, lm_labels=lm_labels)
                            for input_name, input_array in instance.items():
                                datasets[dataset_name][input_name].append(input_array)
                        datasets[dataset_name]["mc_labels"].append(num_candidates - 1)
                        datasets[dataset_name]["n_candidates"] = num_candidates
                    persona = [persona[-1]] + persona[:-1]  # permuted personalities

        tensor_datasets = {"train": [], "valid": []}
        for dataset_name, dataset in datasets.items():
            dataset = self.pad_dataset(dataset, padding=self.pad_id)
            for input_name in constants.MODEL_INPUTS:
                tensor = np.asarray(dataset[input_name])
                if input_name != "mc_labels":
                    shape = [-1, dataset["n_candidates"], *tensor.shape[1:]]
                    tensor = np.reshape(tensor, shape)
                tensor_datasets[dataset_name].append(tensor)

        print("training shapes")
        for arr in tensor_datasets['train']:
            print(arr.shape)
        print('validation shapes')
        for arr in tensor_datasets['valid']:
            print(arr.shape)

        return tensor_datasets['train'], tensor_datasets['valid']
        # train_dataset, valid_dataset = TensorDataset(*tensor_datasets["train"]), TensorDataset(*tensor_datasets["valid"])


    def build_input(self, persona, history, reply, lm_labels=False, with_eos=True, as_ids=True):
        bos = self.bos_id if as_ids else self.bos
        eos = self.eos_id if as_ids else self.eos
        speaker1 = self.speaker1_id if as_ids else self.speaker1
        speaker2 = self.speaker2_id if as_ids else self.speaker2
        sequence = [[bos] + list(chain(*persona))] + history + [reply + ([eos] if with_eos else [])]
        sequence = [sequence[0]] + [[speaker2 if (len(sequence)-i) % 2 else speaker1] + s for i, s in enumerate(sequence[1:])]
        instance = {}
        instance["input_ids"] = list(chain(*sequence))
        instance["token_type_ids"] = [speaker2 if i % 2 else speaker1 for i, s in enumerate(sequence) for _ in s]
        instance["mc_token_ids"] = len(instance["input_ids"]) - 1
        instance["lm_labels"] = [-100] * len(instance["input_ids"])
        if lm_labels:
            instance["lm_labels"] = ([-100] * sum(len(s) for s in sequence[:-1])) + [-100] + sequence[-1][1:]
        return instance


    def get_persona(self, persona):
        persona = models.Persona.objects.get(name=persona)
        if not persona:
            return "persona could not be found"
        persona_statements = [s.format_to_tokens(self.gpt_tokenizer) for s in persona.statements.all()]
        history_statements = [h.format_to_tokens(self.gpt_tokenizer) for h in persona.history.order_by('-previous')]
        
        reply = history_statements.pop()
        history_statements.reverse()
        return persona_statements, history_statements, reply


    def format_data_string(self, string):
        tokenized_string = self.gpt_tokenizer.tokenize(string)
        ids = self.gpt_tokenizer.convert_tokens_to_ids(tokenized_string)
        return ids


    def convert_model_output_to_words(self, output):
        arg_max = tf.argmax(tf.squeeze(output.logits), axis=1) 
        strings = self.gpt_tokenizer.decode(argmax)
        return strings

    def get_distractor(self, persona):
        other = models.History.objects.all().exclude(Persona=persona)
        distractor = random.choice(other).format_to_tokens(self.gpt_tokenizer)
        return distractor

    def pad_dataset(self, dataset, padding=0):
        """ Pad the dataset. This could be optimized by defining a Dataset class and padding at the batch level, but this is simpler. """
        max_l = max(len(x) for x in dataset["input_ids"])
        for name in constants.PADDED_INPUTS:
            dataset[name] = [x + [padding if name != "lm_labels" else -100] * (max_l - len(x)) for x in dataset[name]]
        return dataset

    # def make_prediction(self, words):
    #     result = self.gpt_model.predict(words)
    #     #last = result.logits[0, -1, :]
    #     softmax_val = tf.argmax(tf.squeeze(result.logits), axis=1) 
    #     string = self.gpt_tokenizer.decode(softmax_val)

    #     return string