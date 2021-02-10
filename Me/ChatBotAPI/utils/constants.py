
PATH_TO_UTILS = 'Me/ChatBotAPI/utils/'
PATH_TO_DATA = 'Me/ChatBotAPI/utils/data/'


CHATBOT_MODEL_FILE = 'chatbot_model.h5'
CHATBOT_BACKUP_MODEL_FILE = 'chatbot_backup_model.h5'

SPECIAL_TOKENS = ["<bos>", "<eos>", "<speaker1>", "<speaker2>", "<pad>"]
ATTR_TO_SPECIAL_TOKEN = {'bos_token': '<bos>', 'eos_token': '<eos>', 'pad_token': '<pad>',
                         'additional_special_tokens': ['<speaker1>', '<speaker2>']}

CURRENT_PERSONA = 'Primary'