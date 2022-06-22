function solarnames_list(ss_json) {
    solarnames = []
    for (let key in ss_json) {
        solarnames.push(key)
    }
    return solarnames
}

function autocompleteMatch(input) {
    if (input == '') {
        return [];
    }
    var reg = new RegExp(input)
    var system_names = solarnames_list(ss)
    return system_names.filter(function (term) {
        if (term.match(reg)) {
            return term;
        }
    });
}

function showResults(val) {
    res = document.getElementById("result");
    res.innerHTML = '';
    let list = '';
    let terms = autocompleteMatch(val);
    for (i = 0; i < terms.length; i++) {
        list += '<li>' + terms[i] + '</li>';
    }
    res.innerHTML = '<ul>' + list + '</ul>';
}