/**
 * Function to format and display JSON content in a readable format.
 * @param {string} elementId - The ID of the textarea containing the JSON.
 */
function formatJsonField(elementId) {
    const element = document.getElementById(elementId);
    if (element && element.value) {  // Use `.value` for textareas instead of `.textContent`
        try {
            const jsonContent = JSON.parse(element.value);
            element.value = JSON.stringify(jsonContent, null, 2); // Pretty-print JSON
        } catch (error) {
            console.error(`Error formatting JSON for ${elementId}:`, error);
        }
    }
}

/**
 * Initialize formatting for view_contract page.
 * Formats the JSON fields for funding and deposit instructions.
 */
function initializeViewContractFormatting() {
    formatJsonField('id_funding_instr');  // Corrected ID for funding instructions
    formatJsonField('id_deposit_instr');  // Corrected ID for deposit instructions
    formatJsonField('id_transact_logic');  // Corrected ID for transaction logic
}

// Run the script when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', initializeViewContractFormatting);