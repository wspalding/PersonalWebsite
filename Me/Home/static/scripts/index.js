var chatHistory = [];
var currentRequest = null;

$( document ).ready(function() {
    initChatBot();
    GetChatBotResponse("hello");
    renderChat()
});

function initChatBot() {
    $('.input-text-box').on("keyup", function(e) {
        if(e.keyCode == 13) {
            text = $('.input-text-box').val();
            newMessage = new Message(text, false);

            currentRequest = GetChatBotResponse(text, gatherChatHistory())    
            $('.input-text-box').val("")

            chatHistory.push(newMessage)
            renderChat()

            currentRequest.then(
                function (result) {
                    chatHistory.push(new Message(result.answer, true))
                    renderChat()
                },
                function (error) {
                    chatHistory.push(new Message("an error occured", true, isError=true))
                }
            );
        }
    });
}



function renderChat() {
    textBox = $('.chatbot-text')
    innerHTML = ""
    chatHistory.forEach(m => {
        innerHTML += m.html
    })
    textBox.html(innerHTML);
    textBox.scrollTop(textBox[0].scrollHeight)
}



function GetChatBotResponse(promt, history) {
    return $.ajax({
        type: 'GET',
        url: '/chatbot/get_response', 
        contentType: 'application/json',
        data : {
            prompt: promt,
            history: history
        }
    })
}




function gatherChatHistory() {
    h = []
    currSpeaker = null
    for(var i = 0; i < chatHistory.length; i++) {
        if(i == 0) {
            h.push(chatHistory[i].message);
            currSpeaker = chatHistory[i].isBot;
        }
        else {
            if(currSpeaker == chatHistory[i].isBot){
                h[h.length - 1] += " " + chatHistory[i].message
            }
            else {
                h.push(chatHistory[i].message);
                currSpeaker = chatHistory[i].isBot;
            }
        }
    }
    return h
}


class Message {
    constructor(message, isBot, isError=false){
        this.message = message;
        this.isBot = isBot;
        this.isError = isError;
    }

    get html() {
        var userClass = ((!this.isBot) ? 'person-chat ml-auto' : 'bot-chat');
        if(!this.isError) {
            return `
            <div class="row">
                <div class="chat-bubble ${userClass}">
                    ${this.message}
                </div>
            </div>
            `
        } else {
            return `
            <div class="row chat-bubble ${userClass} error-message">
                ${this.message}
            </div>
            `
        }

    }
}