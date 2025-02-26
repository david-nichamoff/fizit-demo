document.addEventListener("DOMContentLoaded", function () {
    const advancesTableBody = document.querySelector("#advances-table tbody");
    const submitButton = document.querySelector(".submit-row input[type='submit']");
    const advanceForm = document.querySelector(".advance-form");

    function populateAdvancesTable() {
        advancesTableBody.innerHTML = "";
    
        let advances = [];
        for (const contractIdx in advancesList) {
            advances = advances.concat(advancesList[contractIdx]);
        }
    
        if (advances.length === 0) {
            const emptyRow = document.createElement("tr");
            emptyRow.innerHTML = `<td colspan="8" class="empty-result">No advances available.</td>`;
            advancesTableBody.appendChild(emptyRow);
            submitButton.disabled = true;
        } else {
            advances.forEach((advance) => {
                const tooltipContent = advance.bank === "mercury"
                    ? `Account: ${advance.account_name || "N/A"}
                    Recipient: ${advance.recipient_name || "N/A"}`
                    : advance.bank === "token"
                    ? `Funder: ${advance.funder_party_code || "N/A"}<br>Recipient: ${advance.recipient_party_code || "N/A"}<br>Token Symbol: ${advance.token_symbol || "N/A"}`
                    : "No additional details";
            
                const capitalizedContractType = advance.contract_type.charAt(0).toUpperCase() + advance.contract_type.slice(1);
                const uniqueKey = `${advance.contract_type}_${advance.contract_name}_${advance.transact_idx}`;
            
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>
                        <input type="checkbox" class="advance-checkbox" 
                            value="${advance.transact_idx}" 
                            data-unique-key="${uniqueKey}" 
                            data-advance='${JSON.stringify(advance)}' />
                    </td>
                    <td>${capitalizedContractType}</td>
                    <td>${advance.contract_name}</td>
                    <td>${advance.transact_idx}</td>
                    <td>
                        <span class="help-tooltip" data-tooltip="${tooltipContent}">
                            ${advance.bank}
                        </span>
                    </td>
                    <td>${advance.transact_dt}</td>
                    <td>${advance.advance_amt}</td>
                    <td>
                        ${advance.bank === "manual" 
                            ? `<input type="text" class="tx-hash-input" placeholder="Enter TX Hash" 
                                data-unique-key="${uniqueKey}" />`
                            : ""}
                    </td>
                `;
                advancesTableBody.appendChild(row);
            });

            toggleSubmitButton();
        }
    } 

    advanceForm.addEventListener("submit", function (event) {
        const selectedCheckboxes = document.querySelectorAll(".advance-checkbox:checked");
        const advancesInput = document.createElement("input");
        advancesInput.type = "hidden";
        advancesInput.name = "advances";
    
        const selectedAdvances = Array.from(selectedCheckboxes).map((checkbox) => {
            let advanceData = JSON.parse(checkbox.dataset.advance);
            
            if (advanceData.bank === "manual") {
                const uniqueKey = `${advanceData.contract_type}_${advanceData.contract_name}_${advanceData.transact_idx}`;
                const txHashInput = document.querySelector(`.tx-hash-input[data-unique-key="${uniqueKey}"]`);
                advanceData.tx_hash = txHashInput ? txHashInput.value.trim() : "";
            }
        
            return advanceData;
        });
    
        advancesInput.value = JSON.stringify(selectedAdvances);
        advanceForm.appendChild(advancesInput);
        console.log("Submitting advances:", advancesInput.value);
    });

    function toggleSubmitButton() {
        const selectedCheckboxes = document.querySelectorAll(".advance-checkbox:checked");
        submitButton.disabled = selectedCheckboxes.length === 0;
    }

    advancesTableBody.addEventListener("change", function (event) {
        if (event.target.classList.contains("advance-checkbox")) {
            toggleSubmitButton();
        }
    });

    // Tooltip handling (event delegation for efficiency)
    advancesTableBody.addEventListener("mouseover", function (event) {
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

    // Load advances immediately on page load
    populateAdvancesTable();
});