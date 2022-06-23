function autocompleteMatch(input) {
    if (input == '') {
        return [];
    }
    var reg = new RegExp(input.toUpperCase())
    var names = ss
    return names.filter(function (term) {
        if (term.match(reg)) {
            return term;
        }
    });
}

function showResults(val) {
    let res = document.getElementById("result");
    res.innerHTML = '';
    let selections = document.createElement("ul");
    let terms = autocompleteMatch(val);
    for (i = 0; i < terms.length; i++) {
        let li = document.createElement("li");
        li.appendChild(document.createTextNode(terms[i]));
        li.setAttribute("onclick", "update_input('" + terms[i] + "')");
        li.innertext = terms[i]
        selections.appendChild(li);
    }
    if (val.length >= 2 && terms.length > 1) {
        res.innerHTML = selections.innerHTML;

    }
    else if (terms.length == 1 && val != terms[0]) {
        update_input(terms[0])
    }
    else {
        res.innerHTML = "";;

    }
}

function update_input(val) {
    inp = document.getElementById("search");
    inp.value = val;
    showResults(val);
}
