$( document ).ready(function() {
    console.log( "ready!" );
    GetChatBotResponse();
});

function initSubscribeButton() {

}

function GetChatBotResponse() {
    $.ajax({
        type: 'GET',
        url: '/chatbot/build', 
        contentType: 'application/json',
        data : {
            prompt: "test val"
        }
    })
    .done(function(response) {
        if(response.success)
        {
            console.log('success')
        }
        console.log(response)
    })
    .fail(function(error) {
        console.log(error)
    })
}