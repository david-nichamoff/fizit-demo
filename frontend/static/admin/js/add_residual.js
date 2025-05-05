document.addEventListener("DOMContentLoaded", function () {
    const residualsTableBody = document.querySelector("#residuals-table tbody");
    const submitButton = document.querySelector(".submit-row input[type='submit']");
    const residualForm = document.querySelector(".residual-form");

    function populateResidualsTable() {
        residualsTableBody.innerHTML = "";
    
        let residuals = [];
        for (const contractIdx in residualsList) {
            residuals = residuals.concat(residualsList[contractIdx]);
        }
    
        if (residuals.length === 0) {
            const emptyRow = document.createElement("tr");
            emptyRow.innerHTML = `<td colspan="8" class="empty-result">No residuals available.</td>`;
            residualsTableBody.appendChild(emptyRow);
            submitButton.disabled = true;
        } else {
            residuals.forEach((residual) => {
                const tooltipContent = residual.bank === "mercury"
                    ? `Account: ${residual.account_name || "N/A"}
                    Recipient: ${residual.recipient_name || "N/A"}`
                    : residual.bank === "token"
                    ? `Funder: ${residual.funder_party_code || "N/A"}<br>Recipient: ${residual.recipient_party_code || "N/A"}<br>Token Symbol: ${residual.token_symbol || "N/A"}`
                    : "No additional details";
            
                const capitalizedContractType = residual.contract_type.charAt(0).toUpperCase() + residual.contract_type.slice(1);
                const uniqueKey = `${residual.contract_type}_${residual.contract_name}_${residual.settle_idx}`;
            
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>
                        <input type="checkbox" class="residual-checkbox" 
                            value="${residual.settle_idx}" 
                            data-unique-key="${uniqueKey}" 
                            data-residual='${JSON.stringify(residual)}' />
                    </td>
                    <td>${capitalizedContractType}</td>
                    <td>${residual.contract_name}</td>
                    <td>${residual.settle_due_dt}</td>
                    <td>
                        <span class="help-tooltip" data-tooltip="${tooltipContent}">
                            ${residual.bank}
                        </span>
                    </td>
                    <td>${residual.residual_calc_amt}</td>
                    <td>
                        ${residual.bank === "manual" 
                            ? `<input type="text" class="tx-hash-input" placeholder="Enter TX Hash" 
                                data-unique-key="${uniqueKey}" />`
                            : ""}
                    </td>
                `;
                residualsTableBody.appendChild(row);
            });
    
            toggleSubmitButton();
        }
    } 

    residualForm.addEventListener("submit", function (event) {
        const selectedCheckboxes = document.querySelectorAll(".residual-checkbox:checked");
        const residualsInput = document.createElement("input");
        residualsInput.type = "hidden";
        residualsInput.name = "residuals";
    
        const selectedResiduals = Array.from(selectedCheckboxes).map((checkbox) => {
            let residualData = JSON.parse(checkbox.dataset.residual);
            if (residualData.bank === "manual") {
                const uniqueKey = `${residualData.contract_type}_${residualData.contract_name}_${residualData.settle_idx}`;
                const txHashInput = document.querySelector(`.tx-hash-input[data-unique-key="${uniqueKey}"]`);
                residualData.tx_hash = txHashInput ? txHashInput.value.trim() : "";
            }
            return residualData;
        });

        residualsInput.value = JSON.stringify(selectedResiduals);
        residualForm.appendChild(residualsInput);
        console.log("Submitting residuals:", residualsInput.value);
    });

    function toggleSubmitButton() {
        const selectedCheckboxes = document.querySelectorAll(".residual-checkbox:checked");
        submitButton.disabled = selectedCheckboxes.length === 0;
    }

    residualsTableBody.addEventListener("change", function (event) {
        if (event.target.classList.contains("residual-checkbox")) {
            toggleSubmitButton();
        }
    });

    // Tooltip handling (event delegation for efficiency)
    residualsTableBody.addEventListener("mouseover", function (event) {
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

    // Load residuals immediately on page load
    populateResidualsTable();
});