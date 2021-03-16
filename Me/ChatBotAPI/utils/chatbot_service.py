# from django.conf import settings
# from tensorflow.keras.models import load_model

# from ChatBotAPI.utils import constants

# class ChatBotService():
#     def __init__(self, model_file, **kwargs):
#         self.in_debug = settings.DEBUG
#         self.model = load_model(model_file)
#         print(self.model.summary())
#         self.model._make_predict_function()
#         self.load_data()
#         self.lemmatizer = WordNetLemmatizer()
    

#     def getResponse(self, question):
#         ints = self.predict_class(question)
#         res = self.getResponseFromIntents(ints, self.intents)
#         return res


#     def clean_up_sentence(self, sentence):
#         sentence_words = nltk.word_tokenize(sentence)
#         sentence_words = [self.lemmatizer.lemmatize(word.lower()) for word in sentence_words]
#         return sentence_words

#     def load_data(self):
#         self.intents = json.loads(open(constants.PATH_TO_DATA + 'intents.json').read())
#         self.words = pickle.load(open(constants.PATH_TO_DATA + 'words.pkl','rb'))
#         self.classes = pickle.load(open(constants.PATH_TO_DATA + 'classes.pkl','rb'))

#     def bow(self, sentence, words, show_details=True):
#         # tokenize the pattern
#         sentence_words = self.clean_up_sentence(sentence)
#         # bag of words - matrix of N words, vocabulary matrix
#         bag = [0]*len(words)
#         for s in sentence_words:
#             for i,w in enumerate(words):
#                 if w == s:
#                     # assign 1 if current word is in the vocabulary position
#                     bag[i] = 1
#                     if show_details:
#                         print ("found in bag: %s" % w)
#         return(np.array(bag))

#     def predict_class(self, sentence):
#         # filter out predictions below a threshold
#         p = self.bow(sentence, self.words, show_details=False)
#         res = self.model.predict(np.array([p]))[0]
#         ERROR_THRESHOLD = 0.25
#         results = [[i,r] for i,r in enumerate(res) if r>ERROR_THRESHOLD]
#         # sort by strength of probability
#         results.sort(key=lambda x: x[1], reverse=True)
#         return_list = []
#         for r in results:
#             return_list.append({"intent": self.classes[r[0]], "probability": str(r[1])})
#         return return_list

#     def getResponseFromIntents(self, ints, intents_json):
#         tag = ints[0]['intent']
#         list_of_intents = intents_json['intents']
#         for i in list_of_intents:
#             if(i['tag']== tag):
#                 result = random.choice(i['responses'])
#                 break
#         return result
