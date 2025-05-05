document.addEventListener("DOMContentLoaded", function () {
    console.log("Loaded contracts:", contracts);
    console.log("Loaded contract types:", contractTypes);

    const contractTypeDropdown = document.getElementById("id_contract_type");
    const contractDropdown = document.getElementById("id_contract_idx");
    const transactionLogicField = document.getElementById("id_transact_logic");
    const transactionDataField = document.getElementById("id_transact_data");

    function filterContracts() {
        const selectedType = contractTypeDropdown.value.trim().toLowerCase(); // Normalize case
        console.log(`Filtering contracts for type: ${selectedType}`);

        // Ensure contracts have contract_type field
        const filteredContracts = contracts.filter(contract => 
            contract.contract_type.trim().toLowerCase() === selectedType
        );

        console.log("Filtered contracts:", filteredContracts);

        // Clear contract dropdown
        contractDropdown.innerHTML = "";

        if (filteredContracts.length === 0) {
            contractDropdown.innerHTML = `<option value="">No contracts available</option>`;
            transactionLogicField.value = "";
            transactionDataField.value = "{}";
            return;
        }

        // Populate contract dropdown
        filteredContracts.forEach(contract => {
            const option = document.createElement("option");
            option.value = contract.contract_idx;
            option.textContent = `${contract.contract_name}`;
            contractDropdown.appendChild(option);
        });

        // Select first contract by default
        contractDropdown.value = filteredContracts[0].contract_idx;
        updateTransactionFields(filteredContracts[0]);
    }

    function updateTransactionFields(selectedContract) {
        if (selectedContract) {
            transactionLogicField.value = JSON.stringify(selectedContract.transact_logic || {}, null, 2);
            transactionDataField.value = JSON.stringify(selectedContract.pre_transact_data || {}, null, 2);

            console.log("Populated fields:", {
                transact_logic: transactionLogicField.value,
                transact_data: transactionDataField.value,
            });
        } else {
            transactionLogicField.value = "";
            transactionDataField.value = "{}";
        }
    }

    // Ensure the correct default contract type is selected
    contractTypeDropdown.value = defaultContractType;
    
    // Initialize contract dropdown based on the default contract type
    filterContracts();

    // Listen for contract type changes and update both contracts & transaction fields
    contractTypeDropdown.addEventListener("change", function () {
        filterContracts();
        const firstContract = contracts.find(contract => contract.contract_type.trim().toLowerCase() === contractTypeDropdown.value.trim().toLowerCase());
        updateTransactionFields(firstContract);
    });

    // Listen for contract selection changes
    contractDropdown.addEventListener("change", function () {
        const selectedContractIdx = contractDropdown.value;
        const selectedContract = contracts.find(contract => 
            contract.contract_idx == selectedContractIdx &&
            contract.contract_type.trim().toLowerCase() === contractTypeDropdown.value.trim().toLowerCase()
        );

        console.log("Selected contract:", selectedContract);
        updateTransactionFields(selectedContract);
    });
});