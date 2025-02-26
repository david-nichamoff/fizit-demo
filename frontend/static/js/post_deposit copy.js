document.addEventListener("DOMContentLoaded", function () {
    console.log("Loaded contracts:", contracts);
    console.log("Loaded contract types:", contractTypes);
    console.log("Loaded settlements:", settlements);

    const contractTypeDropdown = document.getElementById("id_contract_type");
    const contractDropdown = document.getElementById("id_contract_idx");
    const settlementDropdown = document.getElementById("id_settle_idx");
    const depositForm = document.querySelector(".post-deposit-form");

    function filterContracts() {
        const selectedType = contractTypeDropdown.value.trim().toLowerCase(); // Normalize case
        console.log(`Filtering contracts for type: ${selectedType}`);

        const filteredContracts = contracts.filter(contract => 
            contract.contract_type.trim().toLowerCase() === selectedType
        );

        console.log("Filtered contracts:", filteredContracts);

        contractDropdown.innerHTML = "";

        if (filteredContracts.length === 0) {
            contractDropdown.innerHTML = `<option value="">No contracts available</option>`;
            return;
        }

        filteredContracts.forEach(contract => {
            const option = document.createElement("option");
            option.value = contract.contract_idx;
            option.textContent = `${contract.contract_name}`;
            contractDropdown.appendChild(option);
        });

        if (filteredContracts.length > 0) {
            contractDropdown.value = filteredContracts[0].contract_idx;
            contractDropdown.dispatchEvent(new Event("change")); 
        }
    }

    function filterSettlements() {
        const selectedType = contractTypeDropdown.value.trim();
        const selectedContract = contractDropdown.value.trim();

        console.log(`Filtering settlements for type: ${selectedType}, contract: ${selectedContract}`);

        settlementDropdown.innerHTML = "";

        if (!selectedType || !selectedContract) {
            settlementDropdown.innerHTML = `<option value="">Select a contract first</option>`;
            return;
        }

        const key = `${selectedType}_${selectedContract}`;
        const availableSettlements = settlements[key] || [];

        console.log("Available settlements:", availableSettlements);

        if (availableSettlements.length === 0) {
            settlementDropdown.innerHTML = `<option value="">No settlements available</option>`;
            return;
        }

        availableSettlements.forEach(settlement => {
            const option = document.createElement("option");
            option.value = settlement.settle_idx;
            option.textContent = `Due: ${settlement.settle_due_dt}`;
            settlementDropdown.appendChild(option);
        });

        settlementDropdown.value = availableSettlements.length > 0 ? availableSettlements[0].settle_idx : "";
    }

    // Ensure correct default contract type is selected
    contractTypeDropdown.value = defaultContractType;
    filterContracts();
    filterSettlements();

    contractTypeDropdown.addEventListener("change", function () {
        filterContracts();
        filterSettlements();
    });

    contractDropdown.addEventListener("change", filterSettlements);

    // Log form submission event
    depositForm.addEventListener("submit", function (event) {
        console.log("Post Deposit Form Submitted!");
        console.log("Form data:", new FormData(depositForm));

        // Ensure form validation passes
        if (!depositForm.checkValidity()) {
            console.log("Form validation failed.");
            event.preventDefault();
        }
    });
});