document.addEventListener("DOMContentLoaded", function () {
    console.log("Contract form script loaded.");
    console.log("Loaded contracts:", contracts);

    // Elements
    const contractDropdown = document.getElementById("id_contract_idx");
    const transactionLogicField = document.getElementById("id_transact_logic");
    const transactionDataField = document.getElementById("id_transact_data");

    // Event listener for contract dropdown change
    contractDropdown.addEventListener("change", function () {
        const selectedContractIdx = contractDropdown.value;
        const selectedContract = contracts.find(contract => contract.contract_idx == selectedContractIdx);

        if (selectedContract) {
            // Populate transaction logic as formatted JSON
            transactionLogicField.value = JSON.stringify(selectedContract.transact_logic, null, 2);

            // Populate transaction data as prepopulated JSON if available
            transactionDataField.value = selectedContract.pre_transact_data
                ? JSON.stringify(selectedContract.pre_transact_data, null, 2)
                : "{}";
        } else {
            // Clear fields if no contract is selected
            transactionLogicField.value = "";
            transactionDataField.value = "{}";
        }
    });
});