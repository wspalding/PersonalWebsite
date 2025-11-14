
const roomName = "default";  // or dynamic from template/context
const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
const chatSocket = new WebSocket(
wsScheme + '://' + window.location.host + '/ws/chat/' + roomName + '/'
);
var chatHistory = [];
var requestCount = 0;
var gpu_active = false


$( document ).ready(function() {
    console.log('called');
    initChatBot();
    renderChat();

});

console.log('init');

chatSocket.onopen = function (e) {
console.log("WebSocket connected");
};

chatSocket.onmessage = function (e) {
    const data = JSON.parse(e.data)
    const message = data['message'];
    console.log("Message from server:", message);
    // Update the DOM with new chat text, etc.
    requestCount--;
    chatHistory.push(new Message(message, true))
    renderChat()
};

chatSocket.onclose = function (e) {
console.log("WebSocket closed unexpectedly");
};

// Example send:
function sendMessage(msg) {
chatSocket.send(msg);
}






function renderChat() {
    textBox = $('.chatbot-text')
    innerHTML = ""
    chatHistory.forEach(m => {
        innerHTML += m.html
    })
    if(requestCount > 0) {
        gpu_message = gpu_active ? '' : 'I promise it’s not broken, I’m just saving up for a graphics card.'
        innerHTML += `
        <div class="row">
                <div class="chat-bubble bot-chat">` + gpu_message + `
                    <i class="fa fa-spinner fa-pulse fa-fw"></i>
                </div>
            </div>
        `
    }
    textBox.html(innerHTML);
    textBox.scrollTop(textBox[0].scrollHeight)
}


function initChatBot() {
    $('#input-text-box').on("keyup", function(e) {
        if(e.keyCode == 13) {
            text = $('#input-text-box').val().trim();
            newMessage = new Message(text, false);

            sendMessage(text)
            // console.log(text)
            requestCount++; 
            $('#input-text-box').val("")

            chatHistory.push(newMessage)
            renderChat()

        }
    });
}

class Message {
    constructor(message, isBot, isError=false){
        this.message = message;
        this.isBot = isBot;
        this.isError = isError;
    }

    get html() {
        var userClass = ((!this.isBot) ? 'person-chat ml-auto' : 'bot-chat formatted');
        if(!this.isError) {
            return `
            <div class="row">
                <div class="chat-bubble ${userClass}">
                    ${renderMarkdown(this.message)}
                </div>
            </div>
            `
        } else {
            return `
            <div class="row chat-bubble error-message ${userClass}">
                ${renderMarkdown(this.message)}
            </div>
            `
        }

    }
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function renderMarkdown(text) {
    if (!text) return "";
    let html = escapeHtml(text);

    // Headings (supporting up to ######)
    html = html.replace(/^###### (.*)$/gm, "<h6>$1</h6>");
    html = html.replace(/^##### (.*)$/gm, "<h5>$1</h5>");
    html = html.replace(/^#### (.*)$/gm, "<h4>$1</h4>");
    html = html.replace(/^### (.*)$/gm, "<h3>$1</h3>");
    html = html.replace(/^## (.*)$/gm, "<h2>$1</h2>");
    html = html.replace(/^# (.*)$/gm, "<h1>$1</h1>");

    // Bold **text**
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

    // Italic *text* or _text_
    html = html.replace(/(^|[^*])\*(?!\s)([^*]+?)\*(?!\*)/g, "$1<em>$2</em>");
    html = html.replace(/(^|[^_])_(?!\s)([^_]+?)_(?!_)/g, "$1<em>$2</em>");

    // Inline code `code`
    html = html.replace(/`([^`]+)`/g, "<code>$1</code>");

    // Links [text](url)
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

    return html;
}



// ------------------------------------------------------------------------------------------------------------------
// LEGACY
// ------------------------------------------------------------------------------------------------------------------

// var chatHistory = [];
// var currentRequest = null;
// var requestCount = 0;

// $( document ).ready(function() {
//     initChatBot();
//     currentRequest = GetChatBotResponse("hello");
//     renderChat()
//     requestCount++;
//     currentRequest.then(
//         function (result) {
//             requestCount--;
//             chatHistory.push(new Message(result.answer, true));
//             renderChat();

//         },
//         function (error) {
//             requestCount--;
//             chatHistory.push(new Message("an error occured", true, isError=true));
//             renderChat();
//         }
//     );
//     renderChat()
// });

// function initChatBot() {
//     $('.input-text-box').on("keyup", function(e) {
//         if(e.keyCode == 13) {
//             text = $('.input-text-box').val().trim();
//             newMessage = new Message(text, false);

//             currentRequest = GetChatBotResponse(text, gatherChatHistory())

//             requestCount++; 
//             $('.input-text-box').val("")

//             chatHistory.push(newMessage)
//             renderChat()

//             currentRequest.then(
//                 function (result) {
//                     //console.log("success before --", requestCount)
//                     requestCount--;
//                     if(requestCount == 0) {
//                         chatHistory.push(new Message(result.answer, true))
//                         renderChat()
//                     }
//                 },
//                 function (error) {
//                     //console.log("error before --", requestCount)
//                     requestCount--;
//                     if(requestCount == 0) {
//                         chatHistory.push(new Message("an error occured, please try again", true, isError=true))
//                         renderChat()
//                     }
//                 }
//             );
//         }
//     });
// }



// function renderChat() {
//     textBox = $('.chatbot-text')
//     innerHTML = ""
//     chatHistory.forEach(m => {
//         innerHTML += m.html
//     })
//     if(requestCount > 0) {
//         innerHTML += `
//         <div class="row">
//                 <div class="chat-bubble bot-chat">
//                     <i class="fa fa-spinner fa-pulse fa-fw"></i>
//                 </div>
//             </div>
//         `
//     }
//     textBox.html(innerHTML);
//     textBox.scrollTop(textBox[0].scrollHeight)
// }



// function GetChatBotResponse(promt, history) {
//     return $.ajax({
//         type: 'POST',
//         url: '/chatbot/get_response', 
//         contentType: 'application/json',
//         headers: { "X-CSRFToken": readCookie('csrftoken') },
//         data : JSON.stringify({
//             prompt: promt,
//             history: history,
//             persona: 'Primary'
//         })
//     })
// }




// function gatherChatHistory() {
//     h = []
//     currSpeaker = null
//     for(var i = 0; i < chatHistory.length; i++) {
//         if(i == 0) {
//             h.push(chatHistory[i].message);
//             currSpeaker = chatHistory[i].isBot;
//         }
//         else {
//             if(chatHistory[i].isError) {
//                 continue;
//             }
//             if(currSpeaker == chatHistory[i].isBot){
//                 h[h.length - 1] += " " + chatHistory[i].message
//             }
//             else {
//                 h.push(chatHistory[i].message);
//                 currSpeaker = chatHistory[i].isBot;
//             }
//         }
//     }
//     return h
// }


// class Message {
//     constructor(message, isBot, isError=false){
//         this.message = message;
//         this.isBot = isBot;
//         this.isError = isError;
//     }

//     get html() {
//         var userClass = ((!this.isBot) ? 'person-chat ml-auto' : 'bot-chat');
//         if(!this.isError) {
//             return `
//             <div class="row">
//                 <div class="chat-bubble ${userClass}">
//                     ${this.message}
//                 </div>
//             </div>
//             `
//         } else {
//             return `
//             <div class="row chat-bubble error-message ${userClass}">
//                 ${this.message}
//             </div>
//             `
//         }

//     }
// }

// function readCookie(name) {
//     var nameEQ = name + "=";
//     var ca = document.cookie.split(';');
//     for (var i = 0; i < ca.length; i++) {
//         var c = ca[i];
//         while (c.charAt(0) == ' ') c = c.substring(1, c.length);
//         if(c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length, c.length);
//     }
//     return null;
// }