new gridjs.Grid({
    sort: true,
    pagination: {
        limit: 50
    },
    fixedHeader: true,
    height: '800px',
    data: mv
}).render(document.getElementById("wrapper"));