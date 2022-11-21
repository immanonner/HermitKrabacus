function autocompleteMatch(input) {
    if (input == '') {
        return [];
    };
    var reg = new RegExp(input);
    var names = ns;
    return names.filter(function (term) {
        if (term.match(reg)) {
            return term;
        };
    });
};

function build_selections(terms) {
    let selections = document.createElement("ul");
    for (i = 0; i < terms.length; i++) {
        let li = document.createElement("li");
        li.appendChild(document.createTextNode(terms[i]));
        li.setAttribute("onclick", "update_input(`" + terms[i] + "`)");
        li.innertext = terms[i];
        selections.appendChild(li);
    };
    return selections;
};

function showResults(val) {
    let res = document.getElementById("result");
    res.innerHTML = '';
    if (ns.length <= 10) {
        res.appendChild(build_selections(ns));
        return;
    } else {
        let terms = autocompleteMatch(val);
        let options = build_selections(terms);
        if (terms.length == 1 && val == terms[0]) {
            res.innerHTML = '';
            return;
        } else {
            res.appendChild(options);
            return;
        };
    };
};

function update_input(val) {
    inp = document.getElementById("search");
    inp.value = val;
    showResults(val);
};
