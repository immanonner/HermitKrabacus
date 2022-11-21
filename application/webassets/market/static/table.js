if (document.getElementById("wrapper")) {
    const grid = new gridjs.Grid({
        columns: [
            {
                id: 'myCheckbox',
                name: 'Select',
                width: '3%',
                plugin: {
                    // install the RowSelection plugin
                    component: gridjs.plugins.selection.RowSelection,
                    // RowSelection config
                    props: {
                        // use the "typeName" column as the row identifier
                        id: (row) => [
                            //  0 typeName:
                            row.cell(1).data,
                            // 1 hub_min_price: 
                            row.cell(2).data,
                            //  2 lastPriceAvg: 
                            row.cell(3).data,
                            // 3 order_id: 
                            row.cell(4).data,
                            // 4 velocity: 
                            row.cell(5).data,
                            // 5 saleChance: 
                            row.cell(6).data,
                            // 6 stock_remaining: 
                            row.cell(7).data,
                            // 7 dso: 
                            row.cell(8).data,
                            // 8 ppi: 
                            row.cell(9).data,
                            // 9 rr: 
                            row.cell(10).data,
                            // 10 ppd: 
                            row.cell(11).data,
                        ].join(', ')
                    },
                },
            },
            { name: 'typeName', width: '8%' },
            {
                name: 'hub_min_price',
                formatter: (cell) => `${cell.toLocaleString()}`, width: '5%'
            },
            {
                name: 'lastPriceAvg',
                formatter: (cell) => `${cell.toLocaleString()}`, width: '5%'
            },
            {
                name: 'order_id',
                width: '3%'
            },
            { name: 'velocity', width: '3%' },
            { name: 'saleChance', width: '3%' },
            {
                name: 'stock_remaining',
                formatter: (cell) => `${cell.toLocaleString()}`, width: '3%'
            },
            { name: 'dso', width: '3%' },
            {
                name: 'ppi',
                formatter: (cell) => `${cell.toLocaleString()}`, width: '5%'
            },
            { name: 'rr', width: '3%' },
            {
                name: 'ppd',
                formatter: (cell) => `${cell.toLocaleString()}`, width: '5%'
            }
        ],
        sort: true,
        pagination: {
            limit: 20
        },
        fixedHeader: true,
        height: 'min(fit-content)',
        data: mv,
        search: {
            enabled: true
        }
    }).render(document.getElementById("wrapper"));

    grid.on('ready', () => {
        const copyBtn = document.querySelector('.js-copy-btn');
        const checkboxPlugin = grid.config.plugin.get('myCheckbox');
        copyBtn.addEventListener('click', function (event) {
            // find the plugin with the given plugin ID
            // read the selected rows from the plugin's store
            copyTextToClipboard(checkboxPlugin.props.store.state.rowIds.map((row) => row.split(', ')[0] + ' ' + Math.round(row.split(', ')[4])).join('\r\n'));
        });
        checkboxPlugin.props.store.on('updated', () => {
            let quickView = document.querySelector('#table-info>p');
            let stmt = 'No Items Selected';
            if (!checkboxPlugin.props.store.state.rowIds.length) { return quickView.innerHTML = stmt };
            quickView.innerHTML = '';
            let ppd_sum = checkboxPlugin.props.store.state.rowIds.map((rowId) => parseInt(rowId.split(', ')[10])).reduce((a, b) => a + b, 0);
            let formatted_appraise_items = checkboxPlugin.props.store.state.rowIds.map((row) => row.split(', ')[0] + ' ' + Math.round(row.split(', ')[4])).join('\r\n');
            let appraisal = fetchJanice("https://janice.e-351.com/api/rest/v2/appraisal?market=2&designation=appraisal&pricing=sell&pricingVariant=immediate&persist=false&compactize=true&pricePercentage=1", formatted_appraise_items);
            appraisal.then((data) => {
                let urlParams = new URLSearchParams(window.location.search);
                let url = "https://api.pushx.net//api/quote/JSON/?" + `startSystemName=${urlParams.get('import_hub')}&endSystemName=${urlParams.get('sys_name')}&volume=${Math.round(data.totalPackagedVolume)}&collateral=${data.immediatePrices.totalSellPrice}&apiClient=hermitKrabacus`;
                let pushx = fetchPushX(url);
                pushx.then((d) => {
                    quickView.innerHTML = ` ${checkboxPlugin.props.store.state.rowIds.length}\ Items Selected<br>`
                        + `PPD SUM:\ ${ppd_sum.toLocaleString()}<br>`
                        + `Janice Jita Price:\ ${data.immediatePrices.totalSellPrice.toLocaleString()}<br>`
                        + `ROI:\ ${Math.round((ppd_sum / data.immediatePrices.totalSellPrice) * 100).toLocaleString()}%<br>`
                        + `PushX Rush:\ ${Math.round(d.PriceRush).toLocaleString()}<br>`
                        + `Darkhorse Normal:\ ${Math.round((data.immediatePrices.totalSellPrice * .01) + data.totalPackagedVolume * 350).toLocaleString()}<br>`;
                });
            });
            return quickView.innerHTML = `${checkboxPlugin.props.store.state.rowIds.length}\ Items Selected<br>\ PPD SUM:\ ${ppd_sum.toLocaleString()}<br><br><br><br><br>`;
        });

    });
};