document.addEventListener("DOMContentLoaded", function () {
    const postDepositButton = document.querySelector("input[name='post_deposit']");
    const depositDtInput = document.getElementById("selected-deposit-dt");
    const depositAmtInput = document.getElementById("selected-deposit-amt");
    const settleIdxInput = document.getElementById("selected-settle-idx");

    let depositRadios = []; // Placeholder for dynamic deposits
    let settlementRadios = []; // Placeholder for dynamic settlements

    // Enable or disable the "Post Deposit" button based on selections
    function togglePostDepositButton() {
        const isDepositSelected = !!document.querySelector("input[name='deposit']:checked");
        const isSettlementSelected = !!document.querySelector("input[name='settlement']:checked");

        postDepositButton.disabled = !(isDepositSelected && isSettlementSelected);

        console.log("Deposit selected:", isDepositSelected);
        console.log("Settlement selected:", isSettlementSelected);
    }

    // Update deposit fields dynamically
    function handleDepositSelection(event) {
        const selectedDeposit = JSON.parse(event.target.value);
        depositDtInput.value = selectedDeposit.deposit_dt;
        depositAmtInput.value = selectedDeposit.deposit_amt;

        console.log("Selected deposit:", selectedDeposit);
        togglePostDepositButton();
    }

    // Update settlement fields dynamically
    function handleSettlementSelection(event) {
        const selectedSettlement = JSON.parse(event.target.value);
        settleIdxInput.value = selectedSettlement.settle_idx;

        console.log("Selected settlement:", selectedSettlement);
        togglePostDepositButton();
    }

    // Re-bind radio buttons after "Find Deposits" is clicked
    function bindRadioButtons() {
        depositRadios = document.querySelectorAll("input[name='deposit']");
        settlementRadios = document.querySelectorAll("input[name='settlement']");

        depositRadios.forEach((radio) => {
            radio.addEventListener("change", handleDepositSelection);
        });

        settlementRadios.forEach((radio) => {
            radio.addEventListener("change", handleSettlementSelection);
        });

        console.log("Deposits and settlements updated.");
    }

    // Initial state check
    togglePostDepositButton();

    // Rebind on "Find Deposits" response (use event or callback)
    // This assumes you'll update the table dynamically via AJAX or template reload
    document.querySelector(".deposit-form").addEventListener("submit", function () {
        setTimeout(bindRadioButtons, 500); // Simulate delay after response
    });
});