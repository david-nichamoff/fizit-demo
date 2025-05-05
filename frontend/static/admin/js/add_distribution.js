document.addEventListener("DOMContentLoaded", function () {
    console.log("DistributionsList received from template:", distributionsList); // Debugging

    const distributionsTableBody = document.querySelector("#distributions-table tbody");
    const submitButton = document.querySelector(".submit-row input[type='submit']");
    const distributionForm = document.querySelector(".distribution-form");

    function populateDistributionsTable() {
        distributionsTableBody.innerHTML = "";
    
        let distributions = [];
        for (const contractIdx in distributionsList) {
            distributions = distributions.concat(distributionsList[contractIdx]);
        }
    
        if (distributions.length === 0) {
            const emptyRow = document.createElement("tr");
            emptyRow.innerHTML = `<td colspan="8" class="empty-result">No distributions available.</td>`;
            distributionsTableBody.appendChild(emptyRow);
            submitButton.disabled = true;
        } else {
            distributions.forEach((distribution) => {
                const tooltipContent = distribution.bank === "mercury"
                    ? `Account: ${distribution.account_name || "N/A"}
                    Recipient: ${distribution.recipient_name || "N/A"}`
                    : distribution.bank === "token"
                    ? `Funder: ${distribution.funder_party_code || "N/A"}<br>Recipient: ${distribution.recipient_party_code || "N/A"}<br>Token Symbol: ${distribution.token_symbol || "N/A"}`
                    : "No additional details";
    
                const capitalizedContractType = distribution.contract_type.charAt(0).toUpperCase() + distribution.contract_type.slice(1);
                const uniqueKey = `${distribution.contract_type}_${distribution.contract_name}_${distribution.settle_idx}`;
    
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>
                        <input type="checkbox" class="distribution-checkbox" 
                            value="${distribution.settle_idx}" 
                            data-unique-key="${uniqueKey}" 
                            data-distribution='${JSON.stringify(distribution)}' />
                    </td>
                    <td>${capitalizedContractType}</td>
                    <td>${distribution.contract_name}</td>
                    <td>${distribution.settle_due_dt}</td>
                    <td>
                        <span class="help-tooltip" data-tooltip="${tooltipContent}">
                            ${distribution.bank}
                        </span>
                    </td>
                    <td>${distribution.distribution_calc_amt}</td>
                    <td>
                        ${distribution.bank === "manual" 
                            ? `<input type="text" class="tx-hash-input" placeholder="Enter TX Hash" 
                                data-unique-key="${uniqueKey}" />`
                            : ""}
                    </td>
                `;
                distributionsTableBody.appendChild(row);
            });
    
            toggleSubmitButton();
        }
    } 

    distributionForm.addEventListener("submit", function (event) {
        const selectedCheckboxes = document.querySelectorAll(".distribution-checkbox:checked");
        const distributionsInput = document.createElement("input");
        distributionsInput.type = "hidden";
        distributionsInput.name = "distributions";
    
        const selectedDistributions = Array.from(selectedCheckboxes).map((checkbox) => {
            let distributionData = JSON.parse(checkbox.dataset.distribution);
            if (distributionData.bank === "manual") {
                const uniqueKey = `${distributionData.contract_type}_${distributionData.contract_name}_${distributionData.settle_idx}`;
                const txHashInput = document.querySelector(`.tx-hash-input[data-unique-key="${uniqueKey}"]`);
                distributionData.tx_hash = txHashInput ? txHashInput.value.trim() : "";
            }
            return distributionData;
        });
    
        distributionsInput.value = JSON.stringify(selectedDistributions);
        distributionForm.appendChild(distributionsInput);
        console.log("Submitting distributions:", distributionsInput.value);
    });

    function toggleSubmitButton() {
        const selectedCheckboxes = document.querySelectorAll(".distribution-checkbox:checked");
        submitButton.disabled = selectedCheckboxes.length === 0;
    }

    distributionsTableBody.addEventListener("change", function (event) {
        if (event.target.classList.contains("distribution-checkbox")) {
            toggleSubmitButton();
        }
    });

    // Tooltip handling (event delegation for efficiency)
    distributionsTableBody.addEventListener("mouseover", function (event) {
        const tooltipTrigger = event.target.closest(".help-tooltip");
        if (tooltipTrigger) {
            const tooltipContent = tooltipTrigger.getAttribute("data-tooltip");
            const tooltipElement = document.createElement("div");
            tooltipElement.className = "tooltip";
            tooltipElement.innerHTML = tooltipContent; // Use innerHTML for HTML rendering
            document.body.appendChild(tooltipElement);

            const rect = tooltipTrigger.getBoundingClientRect();
            tooltipElement.style.left = `${rect.left + window.scrollX}px`;
            tooltipElement.style.top = `${rect.top + window.scrollY - tooltipElement.offsetHeight - 10}px`;

            tooltipTrigger.addEventListener("mouseleave", function () {
                tooltipElement.remove();
            });
        }
    });

    // Load distributions immediately on page load
    populateDistributionsTable();
});