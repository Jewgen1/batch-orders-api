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
            <td>
                <button onclick="updateOrderStatus(${order.id}, 'IN_PROGRESS')">IN_PROGRESS</button>
                <button onclick="updateOrderStatus(${order.id}, 'DONE')">DONE</button>
                <button onclick="updateOrderStatus(${order.id}, 'FAILED')">FAILED</button>
            </td>
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

async function updateOrderStatus(orderId, status) {
    await fetch(`/orders/${orderId}/status`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            status: status
        })
    });

    await loadOrders();
}

async function loadEvents() {
    const response = await fetch('/events');
    const events = await response.json();

    const tableBody = document.getElementById('events-table-body');
    tableBody.innerHTML = '';

    for (const event of events) {
        const row = document.createElement('tr');

        row.innerHTML = `
            <td>${event.id}</td>
            <td>${event.event_type}</td>
            <td>${event.message}</td>
            <td>${event.created_at}</td>
        `;

        tableBody.appendChild(row);
    }
}

async function createTestEvent() {
    await fetch('/events/test', {
        method: 'POST'
    });

    await loadEvents();
}

loadMeta();
loadOrders();
loadEvents();

setInterval(loadOrders, 5000);
setInterval(loadEvents, 5000);
