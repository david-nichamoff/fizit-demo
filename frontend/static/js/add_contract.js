document.addEventListener('DOMContentLoaded', () => {
    console.log('Contract form script loaded.');
    console.log('Loaded accounts:', accounts);
    console.log('Loaded recipients:', recipients);
    console.log('Loaded templates:', templates);

    // Fields and DOM elements
    const fundingMethodField = document.getElementById('id_funding_method');
    const fundingTokenSymbolField = document.getElementById('id_funding_token_symbol');
    const fundingAccountField = document.getElementById('id_funding_account');
    const fundingRecipientField = document.getElementById('id_funding_recipient');

    const depositMethodField = document.getElementById('id_deposit_method');
    const depositTokenSymbolField = document.getElementById('id_deposit_token_symbol');
    const depositAccountField = document.getElementById('id_deposit_account');

    const fundingTokenSymbolGroup = document.querySelector('.funding-token-symbol-group');
    const fundingAccountGroup = document.querySelector('.funding-account-group');
    const fundingRecipientGroup = document.querySelector('.funding-recipient-group');

    const depositTokenSymbolGroup = document.querySelector('.deposit-token-symbol-group');
    const depositAccountGroup = document.querySelector('.deposit-account-group');

    const libraryTemplateField = document.getElementById('id_library_template');
    const contractTypeField = document.getElementById('id_contract_type');
    const transactLogicField = document.getElementById('id_transact_logic');

    const form = document.querySelector('.contract-form');

    // Helper: Populate dropdown
    const populateDropdown = (field, data, defaultOptionText) => {
        field.innerHTML = ''; // Clear existing options
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = defaultOptionText;
        field.appendChild(defaultOption);

        data.forEach(item => {
            const option = document.createElement('option');
            option.value = item.id;
            option.textContent = item.name;
            field.appendChild(option);
        });
    };

    // Populate funding and deposit dropdowns
    const initializeDropdowns = () => {
        console.log('Initializing dropdowns...');
        if (fundingAccountField) populateDropdown(fundingAccountField, accounts, 'Select an Account');
        if (fundingRecipientField) populateDropdown(fundingRecipientField, recipients, 'Select a Recipient');
        if (depositAccountField) populateDropdown(depositAccountField, accounts, 'Select an Account');
    };

    // Toggle visibility of funding fields
    const toggleFundingFields = (method) => {
        fundingTokenSymbolGroup.classList.toggle('hidden', method !== 'token');
        fundingAccountGroup.classList.toggle('hidden', method !== 'mercury');
        fundingRecipientGroup.classList.toggle('hidden', method !== 'mercury');
    };

    // Toggle visibility of deposit fields
    const toggleDepositFields = (method) => {
        depositTokenSymbolGroup.classList.toggle('hidden', method !== 'token');
        depositAccountGroup.classList.toggle('hidden', method !== 'mercury');
    };

    // Load templates based on contract type
    const loadTemplates = (contractType) => {
        console.log(`Loading templates for contract type: ${contractType}`);
        libraryTemplateField.innerHTML = ''; // Clear existing options

        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = 'Select a Template';
        libraryTemplateField.appendChild(defaultOption);

        if (!contractType) {
            console.warn('No contract type selected, skipping template loading.');
            return;
        }

        const matchingTemplates = templates.filter(template => template.contract_type === contractType);

        if (matchingTemplates.length > 0) {
            matchingTemplates.forEach(template => {
                const option = document.createElement('option');
                option.value = JSON.stringify(template.logics);
                option.textContent = template.description || 'Unnamed Template';
                libraryTemplateField.appendChild(option);
            });
        } else {
            const noTemplatesOption = document.createElement('option');
            noTemplatesOption.textContent = 'No templates available';
            noTemplatesOption.disabled = true;
            libraryTemplateField.appendChild(noTemplatesOption);
        }
    };

    // Initialize template logic
    const initializeTemplateLogic = () => {
        console.log('Initializing template logic...');
        transactLogicField.value = ''; // Ensure Transaction Logic starts empty

        if (contractTypeField.value) loadTemplates(contractTypeField.value);

        contractTypeField.addEventListener('change', () => {
            transactLogicField.value = ''; // Clear Transaction Logic field
            loadTemplates(contractTypeField.value);
        });

        libraryTemplateField.addEventListener('change', () => {
            const selectedTemplate = libraryTemplateField.value;
            transactLogicField.value = selectedTemplate ? JSON.stringify(JSON.parse(selectedTemplate), null, 2) : '';
        });
    };

    // Event listeners for field visibility
    if (fundingMethodField) {
        toggleFundingFields(fundingMethodField.value); // Trigger visibility on load
        fundingMethodField.addEventListener('change', () => toggleFundingFields(fundingMethodField.value));
    }
    if (depositMethodField) {
        toggleDepositFields(depositMethodField.value); // Trigger visibility on load
        depositMethodField.addEventListener('change', () => toggleDepositFields(depositMethodField.value));
    }

    // Form submission
    form.addEventListener('submit', () => {
        console.log('Submitting form...');
    });

    // Initialize dropdowns and logic
    initializeDropdowns();
    initializeTemplateLogic();
});