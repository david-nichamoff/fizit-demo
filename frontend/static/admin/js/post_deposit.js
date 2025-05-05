document.addEventListener("DOMContentLoaded", function () {
    console.log("Loaded contracts:", contracts);
    console.log("Loaded contract types:", contractTypes);
    console.log("Loaded settlements:", settlements);

    const contractTypeDropdown = document.getElementById("id_contract_type");
    const contractDropdown = document.getElementById("id_contract_idx");
    const settlementDropdown = document.getElementById("id_settle_idx");
    const depositForm = document.querySelector(".post-deposit-form");

    // Capture initially selected values from rendered HTML
    const initialContractType = contractTypeDropdown.value.trim().toLowerCase();
    const initialContractIdx = contractDropdown.value;
    const initialSettleIdx = settlementDropdown.value;

    function filterContracts() {
        const selectedType = contractTypeDropdown.value.trim().toLowerCase();
        console.log(`Filtering contracts for type: ${selectedType}`);

        const filteredContracts = contracts.filter(
            contract => contract.contract_type.trim().toLowerCase() === selectedType
        );

        console.log("Filtered contracts:", filteredContracts);

        const currentVal = contractDropdown.getAttribute("data-initial") || contractDropdown.value;
        contractDropdown.innerHTML = "";

        if (filteredContracts.length === 0) {
            contractDropdown.innerHTML = `<option value="">No contracts available</option>`;
            return;
        }

        filteredContracts.forEach(contract => {
            const option = document.createElement("option");
            option.value = contract.contract_idx;
            option.textContent = contract.contract_name;

            if (contract.contract_idx.toString() === currentVal) {
                option.selected = true;
            }

            contractDropdown.appendChild(option);
        });

        // If no option matched currentVal, select the first one
        if (!filteredContracts.some(c => c.contract_idx.toString() === currentVal)) {
            contractDropdown.value = filteredContracts[0].contract_idx;
        }

        contractDropdown.dispatchEvent(new Event("change")); // Trigger settlement refresh
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
        console.log("Generated key for settlements:", key);
        console.log("Available settlement keys:", Object.keys(settlements));

        if (!(key in settlements)) {
            settlementDropdown.innerHTML = `<option value="">No settlements available</option>`;
            return;
        }

        const availableSettlements = settlements[key];
        console.log("Available settlements:", availableSettlements);

        const currentSettleVal = settlementDropdown.value;

        availableSettlements.forEach(settlement => {
            const option = document.createElement("option");
            option.value = settlement.settle_idx;
            option.textContent = `Due: ${settlement.settle_due_dt}`;

            if (settlement.settle_idx.toString() === currentSettleVal) {
                option.selected = true;
            }

            settlementDropdown.appendChild(option);
        });

        // Fallback to first if nothing matched
        if (!availableSettlements.some(s => s.settle_idx.toString() === currentSettleVal)) {
            settlementDropdown.value = availableSettlements.length > 0 ? availableSettlements[0].settle_idx : "";
        }
    }

    // Initial load
    filterContracts();
    filterSettlements();

    // Bind events
    contractTypeDropdown.addEventListener("change", function () {
        filterContracts();
        filterSettlements();
    });

    contractDropdown.addEventListener("change", filterSettlements);

    // Log form submission
    depositForm.addEventListener("submit", function (event) {
        console.log("Post Deposit Form Submitted!");
        console.log("Form data:", new FormData(depositForm));

        if (!depositForm.checkValidity()) {
            console.log("Form validation failed.");
            event.preventDefault();
        }
    });
});