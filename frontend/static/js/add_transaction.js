document.addEventListener("DOMContentLoaded", function () {
    console.log("Loaded contracts:", contracts);

    const contractDropdown = document.getElementById("id_contract_idx");
    const transactionLogicField = document.getElementById("id_transact_logic");
    const transactionDataField = document.getElementById("id_transact_data");

    // Prepopulate fields for the first contract if available
    if (contracts.length > 0) {
        const initialContract = contracts[0];
        transactionLogicField.value = JSON.stringify(initialContract.transact_logic, null, 2);
        transactionDataField.value = JSON.stringify(initialContract.pre_transact_data, null, 2);

        console.log("Prepopulated fields on load:", {
            transact_logic: transactionLogicField.value,
            transact_data: transactionDataField.value,
        });

        // Set the contract dropdown to the first contract
        if (contractDropdown) {
            contractDropdown.value = initialContract.contract_idx;
        }
    }

    // Add event listener for dropdown changes
    contractDropdown.addEventListener("change", function () {
        const selectedContractIdx = contractDropdown.value;
        const selectedContract = contracts.find(contract => contract.contract_idx == selectedContractIdx);

        console.log("Selected contract:", selectedContract);

        if (selectedContract) {
            transactionLogicField.value = JSON.stringify(selectedContract.transact_logic, null, 2);
            transactionDataField.value = JSON.stringify(selectedContract.pre_transact_data, null, 2);

            console.log("Populated fields on change:", {
                transact_logic: transactionLogicField.value,
                transact_data: transactionDataField.value,
            });
        } else {
            transactionLogicField.value = "";
            transactionDataField.value = "{}";
        }
    });
});