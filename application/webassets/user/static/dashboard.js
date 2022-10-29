if (document.getElementById("stat_grid")) {
    const grid = new gridjs.Grid({
        columns: [
            { name: 'stock_freq', width: '3%' },
            {
                name: 'total_stock', width: '3%',
                // formatter: (cell) => `${cell.toLocaleString()}`, width: '5%'
            },
            {
                name: 'total_cost', width: '3%',
                formatter: (cell) => `${cell.toLocaleString()}`
            },
            { name: 'sell_freq', width: '3%' },
            { name: 'stock_sold', width: '3%' },
            { name: 'total_revenue', width: '3%', formatter: (cell) => `${cell.toLocaleString()}` },

            {
                name: 'on_hand', width: '3%'
                // formatter: (cell) => `${cell.toLocaleString()}`, width: '5%'
            },
            { name: 'typeName', width: '8%' },
            {
                name: 'asp', width: '3%',
                formatter: (cell) => `${cell.toLocaleString()}`
            },
            {
                name: 'abp', width: '3%',
                formatter: (cell) => `${cell.toLocaleString()}`
            },
            {
                name: 'ppi', width: '3%',
                formatter: (cell) => `${cell.toLocaleString()}`
            },
            {
                name: 'rp', width: '3%',
                formatter: (cell) => `${cell.toLocaleString()}`
            },
            {
                name: 'up', width: '3%',
                formatter: (cell) => `${cell.toLocaleString()}`
            },
            {
                name: 'price', width: '3%',
                formatter: (cell) => `${cell.toLocaleString()}`
            },
            {
                name: 'volume_remain', width: '3%'
                // formatter: (cell) => `${cell.toLocaleString()}`, width: '5%'
            },
            {
                name: 'volume_total', width: '3%'
                // formatter: (cell) => `${cell.toLocaleString()}`, width: '5%'
            },
        ],
        sort: true,
        pagination: {
            limit: 50
        },
        fixedHeader: true,
        height: '800px',
        data: mv,
        search: {
            enabled: true
        }
    }).render(document.getElementById("stat_grid"))
};
if (document.getElementById("summary_grid")) {
    const grid = new gridjs.Grid({
        columns: [
            { name: 'name', width: '300px' },
            {
                name: 'ur',
                formatter: (cell) => `${cell.toLocaleString()}`, width: '250px'
            },
            {
                name: 'order_count', width: '250px'
            },
        ],
        sort: true,
        pagination: {
            limit: 50
        },
        fixedHeader: true,
        height: 'fit-content',
        width: '800px',
        data: ov
    }).render(document.getElementById("summary_grid"))
};