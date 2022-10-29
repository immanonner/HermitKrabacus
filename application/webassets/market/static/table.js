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
                            // typeName:
                            row.cell(1).data,
                            // hub_min_price: 
                            row.cell(2).data,
                            // lastPriceAvg: 
                            row.cell(3).data,
                            // order_id: 
                            row.cell(4).data,
                            // velocity: 
                            row.cell(5).data,
                            // saleChance: 
                            row.cell(6).data,
                            // stock_remaining: 
                            row.cell(7).data,
                            // dso: 
                            row.cell(8).data,
                            // be: 
                            row.cell(9).data,
                            // ppi: 
                            row.cell(10).data,
                            // rr: 
                            row.cell(11).data,
                            //ppd:
                            row.cell(12).data].join(', ')
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
                name: 'be',
                formatter: (cell) => `${cell.toLocaleString()}`, width: '5%'
            },
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
        const copyBtn = document.querySelector('.js-copy-btn')
        const checkboxPlugin = grid.config.plugin.get('myCheckbox');
        copyBtn.addEventListener('click', function (event) {
            // find the plugin with the given plugin ID
            // read the selected rows from the plugin's store
            copyTextToClipboard(checkboxPlugin.props.store.state.rowIds.map((row) => row.split(', ')[0] + ' ' + Math.round(row.split(', ')[4])).join('\r\n'));
        });
        checkboxPlugin.props.store.on('updated', () => {
            let quickView = document.querySelector('#table-info>p')
            let stmt = 'No Items Selected'
            if (!checkboxPlugin.props.store.state.rowIds.length) { return quickView.innerHTML = stmt }
            quickView.innerHTML = ''
            s = checkboxPlugin.props.store.state.rowIds.map((rowId) => parseInt(rowId.split(', ')[11])).reduce((a, b) => a + b, 0).toLocaleString();
            // console.log('checkbox updated', checkboxPlugin.props.store.state.rowIds);
            return quickView.innerHTML = `${checkboxPlugin.props.store.state.rowIds.length}\ Items Selected;\ PPD SUM:\ ${s}`

        });

    })
}