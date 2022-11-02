if (document.getElementById("stat_grid")) {
    const grid = new gridjs.Grid({
        columns: [
            { name: "ontime_realized_profit", width: '3%', formatter: (cell) => `${cell.toLocaleString()}` },
            { name: 'ontime_realized_revenue', width: '3%', formatter: (cell) => `${cell.toLocaleString()}` },
            { name: 'ontime_realized_roi', width: '3%' },
            { name: 'ontime_unrealized_profit', width: '3%', formatter: (cell) => `${cell.toLocaleString()}` },
            { name: 'total_unrealized_revenue', width: '3%', formatter: (cell) => `${cell.toLocaleString()}` },
            { name: 'total_realized_revenue', width: '3%', formatter: (cell) => `${cell.toLocaleString()}` },
            { name: 'late_realized_revenue', width: '3%', formatter: (cell) => `${cell.toLocaleString()}` },
            { name: "late_unrealized_revenue", width: '3%', formatter: (cell) => `${cell.toLocaleString()}` },
        ],
        sort: true,
        fixedHeader: true,
        height: 'fit-content',
        width: '1950px',
        data: sv
    }).render(document.getElementById("stat_grid"))
};


if (document.getElementById("order_stat_grid")) {
    const grid = new gridjs.Grid({
        columns: [
            { name: 'name', width: '300px' },
            {
                name: 'order_count', width: '250px'
            },
            {
                name: 'unrealized_revenue',
                formatter: (cell) => `${cell.toLocaleString()}`,
                width: '250px'
            },
        ],
        sort: true,
        pagination: {
            limit: 50
        },
        fixedHeader: true,
        height: 'fit-content',
        width: '800px',
        data: osv
    }).render(document.getElementById("order_stat_grid"))
};

if (document.getElementById("order_grid")) {
    const grid = new gridjs.Grid({
        columns: [
            { name: 'typeName', width: '3%' },
            { name: 'buy_avg_price', formatter: (cell) => `${cell.toLocaleString()}`, width: '3%' },
            { name: 'sell_avg_price', formatter: (cell) => `${cell.toLocaleString()}`, width: '3%' },
            { name: 'current_profit_per_item', formatter: (cell) => `${cell.toLocaleString()}`, width: '3%' },
            { name: 'unrealized_profit', formatter: (cell) => `${cell.toLocaleString()}`, width: '3%' },
            { name: 'remaining_order_value', formatter: (cell) => `${cell.toLocaleString()}`, width: '3%' },
            { name: 'volume_remain', formatter: (cell) => `${cell.toLocaleString()}`, width: '3%' },
            { name: 'shelf_life', width: '3%' },
            { name: 'current_roi', width: '3%' },
        ],

        sort: true,
        pagination: {
            limit: 50
        },
        fixedHeader: true,
        height: '500px',
        width: '1810px',
        data: ov,
        search: true,
    }).render(document.getElementById("order_grid"))
};

if (document.getElementById("market_grid")) {
    const grid = new gridjs.Grid({
        columns: [
            { name: 'typeName', width: '8%' },
            { name: 'shelf_life', width: '3%' },
            { name: 'buy_freq', formatter: (cell) => `${cell != null ? cell.toLocaleString() : cell}`, width: '3%' },
            { name: 'sell_freq', formatter: (cell) => `${cell != null ? cell.toLocaleString() : cell}`, width: '3%' },
            { name: 'buy_quantity', formatter: (cell) => `${cell != null ? cell.toLocaleString() : cell}`, width: '3%' },
            { name: 'sell_quantity', formatter: (cell) => `${cell != null ? cell.toLocaleString() : cell}`, width: '3%' },
            { name: 'buy_total_value', width: '3%', formatter: (cell) => `${cell != null ? cell.toLocaleString() : cell}` },
            { name: 'sell_total_value', width: '3%', formatter: (cell) => `${cell != null ? cell.toLocaleString() : cell}` },
            { name: 'buy_avg_price', width: '3%', formatter: (cell) => `${cell != null ? cell.toLocaleString() : cell}` },
            { name: 'sell_avg_price', width: '3%', formatter: (cell) => `${cell != null ? cell.toLocaleString() : cell}` },
            { name: 'profit_per_item', width: '3%', formatter: (cell) => `${cell != null ? cell.toLocaleString() : cell}` },
            { name: 'realized_profit', width: '3%', formatter: (cell) => `${cell != null ? cell.toLocaleString() : cell}` },
            { name: 'realized_velocity', formatter: (cell) => `${cell != null ? cell.toLocaleString() : cell}`, width: '3%' },
            { name: 'realized_ppd', formatter: (cell) => `${cell != null ? cell.toLocaleString() : cell}`, width: '3%' },
            { name: 'realized_roi', width: '3%' },
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
    }).render(document.getElementById("market_grid"))
};