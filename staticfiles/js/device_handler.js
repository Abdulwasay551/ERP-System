document.addEventListener('DOMContentLoaded', function() {
    function setupProductChangeHandler(row) {
        const productSelect = row.querySelector('[name$="-product"]');
        const deviceInput = row.querySelector('[name$="-device_identifier_value"]');
        
        if (productSelect && deviceInput) {
            productSelect.addEventListener('change', function() {
                // Clear the device identifier when product changes
                deviceInput.value = '';
            });
        }
    }

    // Setup handlers for existing rows
    document.querySelectorAll('.dynamic-saleitems').forEach(setupProductChangeHandler);

    // Watch for new rows being added
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType === 1 && node.classList.contains('dynamic-saleitems')) {
                    setupProductChangeHandler(node);
                }
            });
        });
    });

    // Start observing the inline formset container
    const formset = document.querySelector('.inline-group');
    if (formset) {
        observer.observe(formset, { childList: true, subtree: true });
    }
});
