(function($) {
    'use strict';

    $(document).ready(function() {
        function initializeSelect2() {
            var employeeSelect = $('#id_employee');
            var financeField = $('#id_employee_finance');
            var configField = $('#id_config');
            var loanDeductionField = $('#id_loan_deduction');  // Add loan deduction field

            if (!employeeSelect.length) return;

            // Initialize Select2
            employeeSelect.select2({
                width: '100%',
                placeholder: 'Select an employee'
            });

            if (financeField.length) {
                financeField.select2({
                    width: '100%',
                    placeholder: 'Select finance details'
                });
            }

            if (configField.length) {
                configField.select2({
                    width: '100%',
                    placeholder: 'Select configuration'
                });

                // Auto-select first config
                $.ajax({
                    url: '/get/get_config/',
                    dataType: 'json',
                    success: function(data) {
                        if (data && data.length > 0) {
                            var config = data[0];
                            var option = new Option(
                                `PF: ${config.provident_fund}%, Leaves: ${config.allowed_leaves}, Saturday's: ${config.overtime_saturday_percentage}%, Gazetted's: ${config.overtime_gazetted_percentage}%`,
                                config.id,
                                true,
                                true
                            );
                            
                            configField
                                .append(option)
                                .val(config.id)
                                .trigger('change');
                        }
                    },
                    error: function(xhr, status, error) {
                        console.error('Error fetching config data:', error);
                    }
                });
            }

            // Finance field update function
            async function updateFinanceField() {
                const employeeId = employeeSelect.val();
                if (!employeeId) {
                    financeField.empty().append('<option value="">---------</option>');
                    if (loanDeductionField.length) {
                        loanDeductionField.val('0.00');
                    }
                    $('.employee-finance-inline tbody tr').hide();
                    return;
                }

                try {
                    // Get finance details
                    const financeResponse = await $.ajax({
                        url: '/get/get_employee_finance/',
                        data: { 'employee_id': employeeId },
                        dataType: 'json'
                    });

                    if (financeResponse && financeResponse.length > 0) {
                        const finance = financeResponse[0];
                        
                        // Update hidden finance field
                        const option = new Option(
                            `NS: ${finance.base_salary}Rs, FA: ${finance.fuel_allowance}Rs, SA: ${finance.special_allowance}Rs, Total-PF: ${finance.total_provident_fund}Rs, Bank: ${finance.bank_name}, AC#: ${finance.bank_account_number}`, 
                            finance.id, 
                            true, 
                            true
                        );
                        
                        financeField.empty().append(option).val(finance.id).trigger('change');

                        // Update inline form cells
                        const row = $('.employee-finance-inline tbody tr:first');
                        row.find('td.field-bank_name p').html(finance.bank_name);
                        row.find('td.field-bank_account_number p').html(finance.bank_account_number);
                        row.find('td.field-base_salary p').html(finance.base_salary);
                        row.find('td.field-fuel_allowance p').html(finance.fuel_allowance);
                        row.find('td.field-special_allowance p').html(finance.special_allowance);
                        row.find('td.field-total_provident_fund p').html(finance.total_provident_fund);
                        
                        // Show the row and entire inline section
                        row.show();
                        $('.employee-finance-inline').show();
                        
                        console.log('Updated finance fields:', finance); // Debug logging
                    }

                    // Get loan details
                    const loanResponse = await $.ajax({
                        url: '/get/get_active_loan/',
                        data: { 'employee_id': employeeId },
                        dataType: 'json'
                    });

                    if (loanDeductionField.length) {
                        if (loanResponse && loanResponse.per_month_deduction) {
                            loanDeductionField.val(loanResponse.per_month_deduction);
                        } else {
                            loanDeductionField.val('0.00');
                        }
                    }

                } catch (error) {
                    console.error('Error updating fields:', error);
                    if (loanDeductionField.length) {
                        loanDeductionField.val('0.00');
                    }
                    $('.employee-finance-inline tbody tr').hide();
                }
            }

            employeeSelect.on('change', updateFinanceField);

            // Initial load if employee is pre-selected
            if (employeeSelect.val()) {
                updateFinanceField();
            }
        }

        function handleEmployeeChange(selectElement) {
            const employeeId = selectElement.value;
            if (!employeeId) return;
        
            // Fetch employee finance details
            $.ajax({
                url: '/get/get_employee_finance/',
                data: { 'employee_id': employeeId },
                success: function(data) {
                    if (data && data.length > 0) {
                        const finance = data[0];
                        
                        // Update employee finance inline form
                        const row = $('.employee-finance-inline tbody tr:first');
                        row.find('td.field-bank_name input').val(finance.bank_name);
                        row.find('td.field-bank_account_number input').val(finance.bank_account_number);
                        row.find('td.field-base_salary input').val(finance.base_salary);
                        row.find('td.field-fuel_allowance input').val(finance.fuel_allowance);
                        row.find('td.field-special_allowance input').val(finance.special_allowance);
                        row.find('td.field-total_provident_fund input').val(finance.total_provident_fund);
                        
                        // Show the row
                        row.show();
                    }
                }
            });
        
            // Auto-select config
            $.ajax({
                url: '/get/get_config/',
                success: function(data) {
                    if (data && data.length > 0) {
                        const config = data[0];
                        $('#id_config').val(config.id).trigger('change');
                    }
                }
            });
        }

        initializeSelect2();
        $(document).on('formset:added', initializeSelect2);
    });
})(window.jQuery || django.jQuery);
