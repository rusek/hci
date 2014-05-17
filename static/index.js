window.onload = function() {
    var eventSource = new EventSource("/panel-feed");
    eventSource.onmessage = function(event) {
        var data = JSON.parse(event.data);
        document.body.textContent = data.text;
    };
};
