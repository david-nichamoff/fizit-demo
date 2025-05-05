document.addEventListener("DOMContentLoaded", function () {
    console.log("Loaded contracts:", contracts);
    console.log("Loaded contract types:", contractTypes);

    const contractTypeDropdown = document.getElementById("id_contract_type");
    const contractDropdown = document.getElementById("id_contract_idx");
    const depositForm = document.querySelector(".find-deposits-form");

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
            contractDropdown.dispatchEvent(new Event("change")); // Ensure UI updates
        }
    }

    // Ensure correct default contract type is selected
    contractTypeDropdown.value = defaultContractType;
    filterContracts();

    contractTypeDropdown.addEventListener("change", filterContracts);

    // Log form submission event
    depositForm.addEventListener("submit", function (event) {
        console.log("Find Deposits Form Submitted!");
        console.log("Form data:", new FormData(depositForm));

        // Ensure form validation passes
        if (!depositForm.checkValidity()) {
            console.log("Form validation failed.");
            event.preventDefault();
        }
    });
});