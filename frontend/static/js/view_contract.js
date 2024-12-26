// view_contract.js

/**
 * Function to format and display JSON content in a readable format.
 * @param {string} elementId - The ID of the element containing the JSON.
 */
function formatJsonField(elementId) {
    const element = document.getElementById(elementId);
    if (element && element.textContent) {
        try {
            const jsonContent = JSON.parse(element.textContent);
            element.textContent = JSON.stringify(jsonContent, null, 2);
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
    formatJsonField('funding-instr');
    formatJsonField('deposit-instr');
    formatJsonField('transact-logic');
}

// Run the script when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', initializeViewContractFormatting);