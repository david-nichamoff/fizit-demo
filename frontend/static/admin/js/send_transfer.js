// Dummy send transfer function
function sendTransfer() {
    const fromAddress = document.getElementById('from-address').value;
    const toAddress = document.getElementById('to-address').value;
    const amount = document.getElementById('amount').value;

    if (!fromAddress || !toAddress || !amount) {
        alert("Please fill in all fields.");
        return;
    }

    // Here you would make an AJAX call or submit the form to your backend
    console.log(`Sending ${amount} from ${fromAddress} to ${toAddress}`);

    // Example alert (replace with actual functionality)
    alert(`Transfer of ${amount} AVAX from ${fromAddress} to ${toAddress} initiated!`);

    // Optionally, reset form fields
    document.getElementById('from-address').value = "";
    document.getElementById('to-address').value = "";
    document.getElementById('amount').value = "";
}