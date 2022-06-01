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