async function fetchJanice(url, data) {
    let response = await fetch(url, {
        method: 'POST',
        headers: {
            'content-type': 'text/plain',
            'X-ApiKey': "Lz7zu5CJmbi6Pgvt69vSozzIFR3YsQYO",
            'accept': 'application/json'
        },
        body: data
    });
    let resp = await response.json();
    return resp;
};

async function fetchPushX(url) {
    let response = await fetch(url, {
        method: 'GET'
    });
    let resp = await response.json();
    return resp;
};