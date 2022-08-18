new gridjs.Grid({
    columns: [
        {
            id: 'myCheckbox',
            name: 'Select',
            plugin: {
                // install the RowSelection plugin
                component: gridjs.plugins.selection.RowSelection,
                // RowSelection config
                props: {
                    // use the "email" column as the row identifier
                    id: (row) => row.cell(2).data
                }
            }
        },
        'typeName',
        'hub_min_price',
        'lastPriceAvg',
        'velocity',
        'saleChance',
        'stock_remaining',
        'dso',
        'be',
        'ppi',
        'rr',
        'ppd'
    ],
    sort: true,
    pagination: {
        limit: 50
    },
    fixedHeader: true,
    height: '800px',
    data: mv
}).render(document.getElementById("wrapper"));