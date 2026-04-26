async function loadMeta() {
    const response = await fetch('/meta');
    const data = await response.json();

    document.getElementById('meta').innerHTML = `
        <div><b>App:</b> ${data.display_name}</div>
        <div><b>Version:</b> ${data.version}</div>
        <div><b>Pod:</b> ${data.pod_name}</div>
        <div><b>Node:</b> ${data.node_name}</div>
        <div><b>Namespace:</b> ${data.namespace}</div>
        <div><b>Database:</b> ${data.db_status}</div>
    `;
}

async function loadOrders() {
    const response = await fetch('/orders');
    const orders = await response.json();

    const tableBody = document.getElementById('orders-table-body');
    tableBody.innerHTML = '';

    for (const order of orders) {
        const row = document.createElement('tr');

        row.innerHTML = `
            <td>${order.id}</td>
            <td>${order.order_number}</td>
            <td>${order.status}</td>
            <td>${order.created_at}</td>
        `;

        tableBody.appendChild(row);
    }
}

async function createTestOrder() {
    const orderNumber = 'TEST-' + Date.now();

    await fetch('/orders', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            order_number: orderNumber
        })
    });

    await loadOrders();
}

loadMeta();
loadOrders();

setInterval(loadOrders, 5000);
