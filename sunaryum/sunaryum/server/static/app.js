// static/app.js
let currentWallet = null;

async function createWallet() {
    const response = await fetch('/wallet/new');
    const wallet = await response.json();
    
    currentWallet = wallet;
    document.getElementById('wallet-info').innerHTML = `
        <p>Seed: ${wallet.seed}</p>
        <p>Endereço: ${wallet.address}</p>
        <p>Saldo: <span id="balance">Carregando...</span></p>
    `;
    
    updateBalance();
}

async function updateBalance() {
    if(!currentWallet) return;
    
    const response = await fetch(`/balance/${currentWallet.address}`);
    const balance = await response.json();
    document.getElementById('balance').textContent = balance.balance;
}

document.getElementById('transaction-form').onsubmit = async (e) => {
    e.preventDefault();
    
    const txData = {
        inputs: [{
            address: currentWallet.address,
            txid: 'genesis' // Em produção, isso viria de UTXOs reais
        }],
        outputs: [{
            address: document.getElementById('to').value,
            amount: parseInt(document.getElementById('amount').value)
        }]
    };

    const response = await fetch('/transaction', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(txData)
    });

    if(response.ok) {
        alert('Transação enviada para a mempool!');
        updateMempool();
    }
};

async function startMining() {
    await fetch('/mine', {method: 'POST'});
    alert('Mineração iniciada! Blocos serão gerados a cada 10 segundos');
}

async function updateMempool() {
    const response = await fetch('/mempool');
    const mempool = await response.json();
    
    const mempoolDiv = document.getElementById('mempool');
    mempoolDiv.innerHTML = `<pre>${JSON.stringify(mempool, null, 2)}</pre>`;
}

// Atualizações periódicas
setInterval(() => {
    if(currentWallet) {
        updateBalance();
        updateMempool();
    }
}, 5000);