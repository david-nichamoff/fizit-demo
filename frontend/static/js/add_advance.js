document.addEventListener("DOMContentLoaded", function () {
    const contractDropdown = document.getElementById("id_contract_idx");
    const advancesTableBody = document.querySelector("#advances-table tbody");
    const submitButton = document.querySelector(".submit-row input[type='submit']");
    const advanceForm = document.querySelector(".advance-form");

    // Function to update the advances table and submit button
    function updateAdvancesTable(contractIdx) {
        // Clear existing rows
        advancesTableBody.innerHTML = "";

        // Find the advances for the selected contract
        const advances = advancesByContract[contractIdx] || [];

        if (advances.length === 0) {
            // Display a message when no advances are available
            const emptyRow = document.createElement("tr");
            emptyRow.innerHTML = `
                <td colspan="5" class="empty-result">No advances available for this contract.</td>
            `;
            advancesTableBody.appendChild(emptyRow);
            submitButton.disabled = true;
        } else {
            // Populate the table with advances
            advances.forEach((advance) => {
                const tooltipContent = advance.bank === "mercury"
                    ? `Account: ${advance.account_name || "N/A"} 
                    Recipient: ${advance.recipient_name || "N/A"}`
                    : advance.bank === "token"
                    ? `Funder: ${advance.funder_party_code || "N/A"} 
                    Recipient: ${advance.recipient_party_code || "N/A"} 
                    Token Symbol: ${advance.token_symbol || "N/A"}`
                    : "No additional details";

                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>
                        <input type="checkbox" class="advance-checkbox" value="${advance.transact_idx}" 
                               data-advance='${JSON.stringify(advance)}' />
                    </td>
                    <td>
                        <span class="help-tooltip" data-tooltip="${tooltipContent}">
                            ${advance.transact_idx}
                        </span>
                    </td>
                    <td>${advance.bank}</td>
                    <td>${advance.transact_dt}</td>
                    <td>${advance.advance_amt}</td>
                `;
                advancesTableBody.appendChild(row);
            });

            // Re-check if any advances are selected
            toggleSubmitButton();

            // Enable tooltips
            const tooltips = document.querySelectorAll(".help-tooltip");
            tooltips.forEach((tooltip) => {
                tooltip.addEventListener("mouseenter", function () {
                    const tooltipContent = this.getAttribute("data-tooltip");
                    const tooltipElement = document.createElement("div");
                    tooltipElement.className = "tooltip";
                    tooltipElement.innerHTML = tooltipContent; // Use innerHTML for HTML rendering
                    document.body.appendChild(tooltipElement);

                    const rect = this.getBoundingClientRect();
                    tooltipElement.style.left = `${rect.left + window.scrollX}px`;
                    tooltipElement.style.top = `${rect.top + window.scrollY - tooltipElement.offsetHeight - 10}px`;

                    this.addEventListener("mouseleave", function () {
                        tooltipElement.remove();
                    });
                });
            });
        }
    }

    // Handle contract selection change
    contractDropdown.addEventListener("change", function () {
        const selectedContractIdx = contractDropdown.value;
        updateAdvancesTable(selectedContractIdx);
    });

    // Ensure the submit includes complete advance data
    advanceForm.addEventListener("submit", function (event) {
        const selectedCheckboxes = document.querySelectorAll(".advance-checkbox:checked");
        const advancesInput = document.createElement("input");
        advancesInput.type = "hidden";
        advancesInput.name = "advances";
        advancesInput.value = JSON.stringify(
            Array.from(selectedCheckboxes).map((checkbox) => JSON.parse(checkbox.dataset.advance))
        );
        advanceForm.appendChild(advancesInput);
    });

    // Function to toggle the submit button based on selected checkboxes
    function toggleSubmitButton() {
        const selectedCheckboxes = document.querySelectorAll(".advance-checkbox:checked");
        submitButton.disabled = selectedCheckboxes.length === 0;
    }

    // Add an event listener to handle checkbox changes
    advancesTableBody.addEventListener("change", function (event) {
        if (event.target.classList.contains("advance-checkbox")) {
            toggleSubmitButton();
        }
    });

    // Load advances for the first contract on page load
    const firstContractIdx = contractDropdown.value;
    if (firstContractIdx) {
        updateAdvancesTable(firstContractIdx);
    }
});