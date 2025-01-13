document.addEventListener("DOMContentLoaded", function () {
    const contractDropdown = document.getElementById("id_contract_idx");
    const residualsTableBody = document.querySelector("#residuals-table tbody");
    const submitButton = document.querySelector(".submit-row input[type='submit']");
    const residualForm = document.querySelector(".residual-form");

    // Function to update the residuals table and submit button
    function updateResidualsTable(contractIdx) {
        // Clear existing rows
        residualsTableBody.innerHTML = "";

        // Find the residuals for the selected contract
        const residuals = residualsByContract[contractIdx] || [];

        console.log(`Loading ${residuals.length} residuals for contract ${contractIdx}`);

        if (residuals.length === 0) {
            // Display a message when no residuals are available
            const emptyRow = document.createElement("tr");
            emptyRow.innerHTML = `
                <td colspan="5" class="empty-result">No residuals available for this contract.</td>
            `;
            residualsTableBody.appendChild(emptyRow);
            submitButton.disabled = true;
        } else {
            // Populate the table with residuals
            residuals.forEach((residual) => {
                const tooltipContent = residual.bank === "mercury"
                    ? `Account: ${residual.account_name || "N/A"} 
                    Recipient: ${residual.recipient_name || "N/A"}`
                    : residual.bank === "token"
                    ? `Funder: ${residual.funder_party_code || "N/A"} 
                    Recipient: ${residual.recipient_party_code || "N/A"} 
                    Token Symbol: ${residual.token_symbol || "N/A"}`
                    : "No additional details";

                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>
                        <input type="checkbox" class="residual-checkbox" value="${residual.transact_idx}" 
                               data-residual='${JSON.stringify(residual)}' />
                    </td>
                    <td>${residual.bank}</td>
                    <td>${residual.settle_idx}</td>
                    <td>${residual.residual_calc_amt}</td>
                `;
                residualsTableBody.appendChild(row);
            });

            // Re-check if any residuals are selected
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
        updateResidualsTable(selectedContractIdx);
    });

    // Ensure the submit includes complete residual data
    residualForm.addEventListener("submit", function (event) {
        const selectedCheckboxes = document.querySelectorAll(".residual-checkbox:checked");
        const residualsInput = document.createElement("input");
        residualsInput.type = "hidden";
        residualsInput.name = "residuals";
        residualsInput.value = JSON.stringify(
            Array.from(selectedCheckboxes).map((checkbox) => JSON.parse(checkbox.dataset.residual))
        );
        residualForm.appendChild(residualsInput);
    });

    // Function to toggle the submit button based on selected checkboxes
    function toggleSubmitButton() {
        const selectedCheckboxes = document.querySelectorAll(".residual-checkbox:checked");
        submitButton.disabled = selectedCheckboxes.length === 0;
    }

    // Add an event listener to handle checkbox changes
    residualsTableBody.addEventListener("change", function (event) {
        if (event.target.classList.contains("residual-checkbox")) {
            toggleSubmitButton();
        }
    });

    // Load residuals for the first contract on page load
    const firstContractIdx = contractDropdown.value;
    if (firstContractIdx) {
        updateResidualsTable(firstContractIdx);
    }
});