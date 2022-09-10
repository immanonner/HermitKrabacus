// Navigation Link Current Page Class
// Implemented JS Solution due to researching why pseudo :visited didn't work:
// http://joelcalifa.com/blog/revisiting-visited <-derived from Joe

function setCurrentPageClass() {
    const nav_links = document.querySelectorAll("#menu>a");
    Array.from(nav_links).forEach(link => {
        if (link.host == window.location.host && link.pathname == window.location.pathname ||
            window.location.pathname == '/' && link.pathname == "/home" ||
            window.location.pathname == '/index' && link.pathname == "/home") {
            link.classList.add("currentPage");
        };
    });
};
setCurrentPageClass();

function fallbackCopyTextToClipboard(text) {
    var textArea = document.createElement("textarea");
    textArea.value = text;

    // Avoid scrolling to bottom
    textArea.style.top = "0";
    textArea.style.left = "0";
    textArea.style.position = "fixed";

    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
        var successful = document.execCommand('copy');
        var msg = successful ? 'successful' : 'unsuccessful';
        console.log('Fallback: Copying text command was ' + msg);
    } catch (err) {
        console.error('Fallback: Oops, unable to copy', err);
    }

    document.body.removeChild(textArea);
}
function copyTextToClipboard(text) {
    if (!navigator.clipboard) {
        fallbackCopyTextToClipboard(text);
        return;
    }
    navigator.clipboard.writeText(text).then(function () {
        console.log('Async: Copying to clipboard was successful!');
    }, function (err) {
        console.error('Async: Could not copy text: ', err);
    });
}