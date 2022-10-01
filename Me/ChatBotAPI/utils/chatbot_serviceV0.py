import tarfile
import torch
import torch.nn.functional as F

from itertools import chain

from ChatBotAPI.utils import constants
from ChatBotAPI import models
from transformers import cached_path
from transformers import OpenAIGPTLMHeadModel, OpenAIGPTTokenizer #, GPT2LMHeadModel, GPT2Tokenizer

class ChatBotServiceV0():
    def __init__(self, **kwargs) -> None:
        # print('INITIALIZING CHATBOT SERVICE')
        self.model_checkpoint = kwargs.get('model_checkpoint')
        if not self.model_checkpoint:
            self.model_checkpoint = self.download_pretrained_model()
        tokenizer_class = OpenAIGPTTokenizer
        model_class = OpenAIGPTLMHeadModel
        self.tokenizer = tokenizer_class.from_pretrained(self.model_checkpoint)
        self.model = model_class.from_pretrained(self.model_checkpoint).eval()
        # print('MODEL AND TOKENIZER LOADED')

        self.bos, self.eos, self.speaker1, self.speaker2, self.pad = constants.SPECIAL_TOKENS
        self.bos_id = self.tokenizer.convert_tokens_to_ids(self.bos)
        self.eos_id = self.tokenizer.convert_tokens_to_ids(self.eos)
        self.speaker1_id = self.tokenizer.convert_tokens_to_ids(self.speaker1)
        self.speaker2_id = self.tokenizer.convert_tokens_to_ids(self.speaker2)
        self.pad_id = self.tokenizer.convert_tokens_to_ids(self.pad)

        # args
        self.max_history = 4
        self.min_length = 1
        self.max_length = 20
        self.temperature = 0.7
        self.top_k = 0.
        self.top_p = 0.9
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.no_sample = False

    def get_response(self, persona, raw_text, history):
        persona_statements, _, _ = self.get_persona(persona)
        tokens = [self.tokenizer.tokenize(p) for p in persona_statements]
        persona_tokens = [self.tokenizer.convert_tokens_to_ids(t) for t in tokens]
        if not history:
            history = []
        history = [self.tokenizer.encode(h) for h in history]
        history.append(self.tokenizer.encode(raw_text))
        with torch.no_grad():
            out_ids = self.sample_sequence(persona_tokens, history)
        history.append(out_ids)
        history = history[-(2*self.max_history+1):]
        out_text = self.tokenizer.decode(out_ids, skip_special_tokens=True)
        return out_text


    def sample_sequence(self, persona_statements, history, current_output=None):
        special_tokens_ids = self.tokenizer.convert_tokens_to_ids(constants.SPECIAL_TOKENS)
        if current_output is None:
            current_output = []

        for i in range(self.max_length):
            instance = self.build_input(persona_statements, history, current_output, self.tokenizer, with_eos=False)

            input_ids = torch.tensor(instance["input_ids"], device=self.device).unsqueeze(0)
            token_type_ids = torch.tensor(instance["token_type_ids"], device=self.device).unsqueeze(0)

            logits = self.model(input_ids, token_type_ids=token_type_ids)
            # if isinstance(logits, tuple):  # for gpt2 and maybe others
            logits = logits[0]
            logits = logits[0, -1, :] / self.temperature
            logits = self.top_filtering(logits, top_k=self.top_k, top_p=self.top_p)
            probs = F.softmax(logits, dim=-1)

            prev = torch.topk(probs, 1)[1] if self.no_sample else torch.multinomial(probs, 1)
            if i < self.min_length and prev.item() in special_tokens_ids:
                while prev.item() in special_tokens_ids:
                    if probs.max().item() == 1:
                        # warnings.warn("Warning: model generating special token with probability 1.")
                        break  # avoid infinitely looping over special token
                    prev = torch.multinomial(probs, num_samples=1)

            if prev.item() in special_tokens_ids:
                break
            current_output.append(prev.item())

        return current_output

    def get_persona(self, persona):
        persona = models.Persona.objects.get(name=persona)
        if not persona:
            return "persona could not be found"
        # persona_statements = [s.format_to_tokens(self.tokenizer) for s in persona.statements.all()]
        # history_statements = [h.format_to_tokens(self.tokenizer) for h in persona.history.order_by('-previous')]
        persona_statements = [str(s) for s in persona.statements.all()]
        history_statements = [str(h) for h in persona.history.order_by('-previous')]

        reply = history_statements.pop()
        history_statements.reverse()
        return persona_statements, history_statements, reply

    def download_pretrained_model(self):
        """ Download and extract finetuned model from S3 """
        resolved_archive_file = cached_path(constants.HF_FINETUNED_MODEL)
        with tarfile.open(resolved_archive_file, 'r:gz') as archive:
            
            import os
            
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner) 
                
            
            safe_extract(archive, constants.PATH_TO_MODELS)
        return constants.PATH_TO_MODELS

    def top_filtering(self, logits, top_k=0., top_p=0.9, threshold=-float('Inf'), filter_value=-float('Inf')):
        """ Filter a distribution of logits using top-k, top-p (nucleus) and/or threshold filtering
            Args:
                logits: logits distribution shape (vocabulary size)
                top_k: <=0: no filtering, >0: keep only top k tokens with highest probability.
                top_p: <=0.0: no filtering, >0.0: keep only a subset S of candidates, where S is the smallest subset
                    whose total probability mass is greater than or equal to the threshold top_p.
                    In practice, we select the highest probability tokens whose cumulative probability mass exceeds
                    the threshold top_p.
                threshold: a minimal threshold to keep logits
        """
        assert logits.dim() == 1  # Only work for batch size 1 for now - could update but it would obfuscate a bit the code
        top_k = min(top_k, logits.size(-1))
        if top_k > 0:
            # Remove all tokens with a probability less than the last token in the top-k tokens
            indices_to_remove = logits < torch.topk(logits, top_k)[0][..., -1, None]
            logits[indices_to_remove] = filter_value

        if top_p > 0.0:
            # Compute cumulative probabilities of sorted tokens
            sorted_logits, sorted_indices = torch.sort(logits, descending=True)
            cumulative_probabilities = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)

            # Remove tokens with cumulative probability above the threshold
            sorted_indices_to_remove = cumulative_probabilities > top_p
            # Shift the indices to the right to keep also the first token above the threshold
            sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
            sorted_indices_to_remove[..., 0] = 0

            # Back to unsorted indices and set them to -infinity
            indices_to_remove = sorted_indices[sorted_indices_to_remove]
            logits[indices_to_remove] = filter_value

        indices_to_remove = logits < threshold
        logits[indices_to_remove] = filter_value

        return logits

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