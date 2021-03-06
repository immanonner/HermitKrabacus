function autocompleteMatch(input) {
    if (input == '') {
        return [];
    }
    var reg = new RegExp(input.toUpperCase())
    var names = ns
    return names.filter(function (term) {
        if (term.match(reg)) {
            return term;
        }
    });
}

function build_selections(terms) {
    let selections = document.createElement("ul");
    for (i = 0; i < terms.length; i++) {
        let li = document.createElement("li");
        li.appendChild(document.createTextNode(terms[i]));
        li.setAttribute("onclick", "update_input('" + terms[i] + "')");
        li.innertext = terms[i]
        selections.appendChild(li);
    }
    return selections
}

function showResults(val) {
    let res = document.getElementById("result");
    res.innerHTML = '';
    if (ns.length <= 5) {
        res.appendChild(build_selections(ns))
    } else {
        let terms = autocompleteMatch(val)
        let options = build_selections(terms)
        if (terms.length == 1 && val == terms[0]) {
            res.innerHTML = "";
        }
        else {
            res.appendChild(options);
        }
    }
}

function update_input(val) {
    inp = document.getElementById("search");
    inp.value = val;
    showResults(val);
}
