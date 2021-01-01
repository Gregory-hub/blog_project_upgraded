$(function () {
    let nav = $("#nav");
    let navToggle = $("#navToggle");

    navToggle.on("click", function(event){
        event.preventDefault();
        nav.toggleClass("show");
    });

});

document.getElementById("photobtn").onclick = function(event){
    event.preventDefault();
    document.getElementById("searitem").style.display = "block";
};

let report_button = $("#report");
let author_name = $(".intro__auth").text()
let article_name = $(".intro__title").text()

report_button.click(function () {
    var xhr = new XMLHttpRequest()
    xhr.open('GET', 'http://localhost:8000/' + author_name + '/' + article_name + '/report/')

    xhr.onreadystatechange = function(){
        if(xhr.readyState === 4 && xhr.status === 200){
            response = JSON.parse(xhr.response)

            let message = response['message']
            let message_box = $(".message")

            message_box.text(message)

            // insert here

        }
    }
    xhr.send()
})