
PATH_TO_UTILS = 'Me/ChatBotAPI/utils/'
PATH_TO_DATA = 'Me/ChatBotAPI/utils/data/'


CHATBOT_MODEL_FILE = 'chatbot_model.h5'
CHATBOT_BACKUP_MODEL_FILE = 'chatbot_backup_model.h5'

SPECIAL_TOKENS = ["<bos>", "<eos>", "<speaker1>", "<speaker2>", "<pad>"]
ATTR_TO_SPECIAL_TOKEN = {'bos_token': '<bos>', 'eos_token': '<eos>', 'pad_token': '<pad>',
                         'additional_special_tokens': ['<speaker1>', '<speaker2>']}
MODEL_INPUTS = ["input_ids", "mc_token_ids", "lm_labels", "mc_labels", "token_type_ids"]
PADDED_INPUTS = ["input_ids", "lm_labels", "token_type_ids"]


CURRENT_PERSONA = 'Primary'

PERSONACHAT_DATASET_PATH = PATH_TO_DATA + 'personachat_self_original.json'
PERSONACHAT_FORMATTED_DATASET_PATH = PATH_TO_DATA + 'personachat_formatted_ids.json'
# PERSONACHAT_TRAIN_DATA_AS_NUMPY = PATH_TO_DATA + 'personachat_train_numpy.'