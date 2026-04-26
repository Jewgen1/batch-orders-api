async function loadMeta() {
    const response = await fetch('/meta');
    const data = await response.json();
    document.getElementById('meta').textContent = JSON.stringify(data, null, 2);
}

async function loadOrders() {
    const response = await fetch('/orders');
    const data = await response.json();
    document.getElementById('orders').textContent = JSON.stringify(data, null, 2);
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
