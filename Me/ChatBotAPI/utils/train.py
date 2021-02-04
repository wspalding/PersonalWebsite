import nltk
from nltk.stem import WordNetLemmatizer
import json
import pickle

import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Activation, Dropout
from tensorflow.keras.optimizers import SGD
import random

from ChatBotAPI.utils import constants


nltk.download('punkt')
nltk.download('wordnet')

lemmatizer = WordNetLemmatizer()


def build_words_and_classes():
    words=[]
    classes = []
    documents = []
    ignore_words = ['?', '!']
    data_file = open(constants.PATH_TO_DATA + 'intents.json').read() # move to use SQL
    intents = json.loads(data_file)

    for intent in intents['intents']:
        for pattern in intent['patterns']:

            # take each word and tokenize it
            w = nltk.word_tokenize(pattern)
            words.extend(w)
            # adding documents
            documents.append((w, intent['tag']))

            # adding classes to our class list
            if intent['tag'] not in classes:
                classes.append(intent['tag'])

    words = [lemmatizer.lemmatize(w.lower()) for w in words if w not in ignore_words]
    words = sorted(list(set(words)))

    classes = sorted(list(set(classes)))

    print (len(documents), "documents")

    print (len(classes), "classes", classes)

    print (len(words), "unique lemmatized words", words)

    pickle.dump(words,open(constants.PATH_TO_DATA + 'words.pkl','wb'))
    pickle.dump(classes,open(constants.PATH_TO_DATA + 'classes.pkl','wb'))


def build_model():
    pass

def train():
    pass
