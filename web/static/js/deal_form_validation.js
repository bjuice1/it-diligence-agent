/**
 * Deal Form Validation - Enforce deal type selection
 *
 * This module provides client-side validation for deal creation forms
 * to ensure deal_type is always selected before submission.
 *
 * Features:
 * - Prevents form submission if deal type not selected
 * - Shows confirmation dialog for carve-out/divestiture (high-risk types)
 * - Provides visual feedback on deal type selection
 * - Updates help text dynamically based on selection
 *
 * Usage:
 *   Include this script in any page with a deal creation form
 *   that has an element with id="deal_type" or id="deal-type"
 */

(function() {
    'use strict';

    // Configuration
    const VALID_DEAL_TYPES = ['acquisition', 'carveout', 'divestiture'];

    const DEAL_TYPE_DESCRIPTIONS = {
        'acquisition': 'System will recommend consolidation synergies (merge target infrastructure into buyer)',
        'carveout': 'System will focus on separation costs and TSA exposure (build standalone infrastructure)',
        'divestiture': 'System will calculate extraction costs (untangle from parent systems)'
    };

    const CONFIRMATION_MESSAGES = {
        'carveout': 'You selected CARVE-OUT.\n\n' +
                   'This will analyze the deal as a SEPARATION (not integration).\n' +
                   'System will calculate standalone build-out costs.\n\n' +
                   'Is this correct?',
        'divestiture': 'You selected DIVESTITURE.\n\n' +
                      'This will analyze the deal as a SEPARATION (not integration).\n' +
                      'System will calculate extraction and untangling costs.\n\n' +
                      'Is this correct?'
    };

    /**
     * Initialize validation on a deal form
     * @param {HTMLFormElement} form - The form element to validate
     * @param {string} dealTypeSelectId - ID of the deal type select element
     */
    function initializeDealFormValidation(form, dealTypeSelectId) {
        if (!form) return;

        const dealTypeSelect = document.getElementById(dealTypeSelectId);
        if (!dealTypeSelect) {
            console.warn(`Deal type select with ID "${dealTypeSelectId}" not found`);
            return;
        }

        // Add form submission handler
        form.addEventListener('submit', function(e) {
            if (!validateDealType(dealTypeSelect)) {
                e.preventDefault();
                return false;
            }

            if (!confirmHighRiskDealType(dealTypeSelect.value)) {
                e.preventDefault();
                return false;
            }

            return true;
        });

        // Add change handler for dynamic help text
        const helpElement = document.getElementById(dealTypeSelectId + '-help');
        if (helpElement) {
            dealTypeSelect.addEventListener('change', function() {
                updateHelpText(dealTypeSelect.value, helpElement);
            });
        }

        // Add visual indicator on change
        dealTypeSelect.addEventListener('change', function() {
            updateVisualIndicator(dealTypeSelect.value);
        });
    }

    /**
     * Validate that a deal type is selected
     * @param {HTMLSelectElement} selectElement - The select element to validate
     * @returns {boolean} True if valid, false otherwise
     */
    function validateDealType(selectElement) {
        const value = selectElement.value;

        if (!value || value === '') {
            alert('Deal type is required. Please select Acquisition, Carve-Out, or Divestiture.');
            selectElement.focus();
            return false;
        }

        if (!VALID_DEAL_TYPES.includes(value)) {
            alert(`Invalid deal type: ${value}. Must be one of: ${VALID_DEAL_TYPES.join(', ')}.`);
            selectElement.focus();
            return false;
        }

        return true;
    }

    /**
     * Show confirmation dialog for high-risk deal types
     * @param {string} dealType - The selected deal type
     * @returns {boolean} True if user confirmed or type is low-risk, false if cancelled
     */
    function confirmHighRiskDealType(dealType) {
        if (dealType === 'carveout' || dealType === 'divestiture') {
            return confirm(CONFIRMATION_MESSAGES[dealType]);
        }
        return true;
    }

    /**
     * Update help text based on selected deal type
     * @param {string} dealType - The selected deal type
     * @param {HTMLElement} helpElement - The help text element
     */
    function updateHelpText(dealType, helpElement) {
        if (!helpElement) return;

        const description = DEAL_TYPE_DESCRIPTIONS[dealType];
        if (description) {
            helpElement.textContent = description;
            helpElement.style.display = 'block';
        } else {
            helpElement.textContent = '';
            helpElement.style.display = 'none';
        }
    }

    /**
     * Update visual indicator for deal type selection
     * @param {string} dealType - The selected deal type
     */
    function updateVisualIndicator(dealType) {
        const indicator = document.querySelector('.deal-type-indicator');
        if (!indicator) return;

        const indicators = {
            'acquisition': {
                text: 'Integration Mode',
                class: 'bg-info'
            },
            'carveout': {
                text: 'Separation Mode',
                class: 'bg-warning'
            },
            'divestiture': {
                text: 'Divestiture Mode',
                class: 'bg-warning'
            }
        };

        const config = indicators[dealType];
        if (config) {
            indicator.textContent = config.text;
            indicator.className = 'deal-type-indicator ' + config.class;
        }
    }

    // Auto-initialize on DOM ready
    document.addEventListener('DOMContentLoaded', function() {
        // Try common form IDs
        const formIds = ['new-deal-form', 'deal-form', 'newDealForm'];
        const selectIds = ['deal-type', 'deal_type', 'modal-deal-type'];

        for (const formId of formIds) {
            const form = document.getElementById(formId);
            if (form) {
                // Find the select element
                for (const selectId of selectIds) {
                    const select = document.getElementById(selectId);
                    if (select) {
                        initializeDealFormValidation(form, selectId);
                        console.log(`Deal form validation initialized for form: ${formId}, select: ${selectId}`);
                        break;
                    }
                }
            }
        }
    });

    // Export for manual initialization if needed
    window.DealFormValidation = {
        initialize: initializeDealFormValidation,
        validateDealType: validateDealType,
        confirmHighRiskDealType: confirmHighRiskDealType
    };
})();
