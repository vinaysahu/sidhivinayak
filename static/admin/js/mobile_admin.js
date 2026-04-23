document.addEventListener('DOMContentLoaded', function() {
    
    // a) DATA-LABEL injection for card layout
    function injectDataLabels() {
        const resultList = document.getElementById('result_list');
        if (resultList) {
            const headers = Array.from(resultList.querySelectorAll('thead th')).map(th => {
                // Get text content, excluding any hidden elements or sorting icons
                return th.innerText.split('\n')[0].trim();
            });

            const rows = resultList.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const cells = row.querySelectorAll('td');
                cells.forEach((td, index) => {
                    if (headers[index]) {
                        td.setAttribute('data-label', headers[index]);
                    }
                });
            });
        }

        // e) INLINE TABLE responsive injection
        const tabularInlines = document.querySelectorAll('.tabular');
        tabularInlines.forEach(inline => {
            const tableHeaders = Array.from(inline.querySelectorAll('thead th')).map(th => th.innerText.trim());
            const inlineRows = inline.querySelectorAll('tbody tr.form-row');
            inlineRows.forEach(row => {
                const inlineCells = row.querySelectorAll('td');
                inlineCells.forEach((td, index) => {
                    if (tableHeaders[index]) {
                        td.setAttribute('data-label', tableHeaders[index]);
                    }
                });
            });
        });
    }

    // b) SIDEBAR TOGGLE
    function setupSidebarToggle() {
        const navSidebar = document.getElementById('nav-sidebar');
        const content = document.getElementById('content');
        
        if (navSidebar && !document.getElementById('mobile-nav-toggle')) {
            const toggleBtn = document.createElement('button');
            toggleBtn.id = 'mobile-nav-toggle';
            toggleBtn.innerHTML = '☰ Menu';
            
            // Insert before content or as first child of header
            const header = document.getElementById('header');
            if (header) {
                header.appendChild(toggleBtn);
            } else {
                document.body.prepend(toggleBtn);
            }

            toggleBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                document.body.classList.toggle('mobile-nav-open');
            });

            // Close when clicking outside
            document.addEventListener('click', function(e) {
                if (document.body.classList.contains('mobile-nav-open')) {
                    if (!navSidebar.contains(e.target) && e.target !== toggleBtn) {
                        document.body.classList.remove('mobile-nav-open');
                    }
                }
            });
        }
    }

    // c) FILTER TOGGLE
    function setupFilterToggle() {
        const filter = document.getElementById('changelist-filter');
        if (filter && !document.getElementById('filter-toggle')) {
            const h2 = filter.querySelector('h2');
            const toggleBtn = document.createElement('button');
            toggleBtn.id = 'filter-toggle';
            toggleBtn.innerHTML = '▼ Filters';
            
            filter.insertBefore(toggleBtn, filter.firstChild);

            toggleBtn.addEventListener('click', function() {
                filter.classList.toggle('filter-open');
                this.innerHTML = filter.classList.contains('filter-open') ? '▲ Filters' : '▼ Filters';
            });
        }
    }

    // Initialize all mobile features
    function initMobileFeatures() {
        if (window.innerWidth < 768) {
            injectDataLabels();
            setupSidebarToggle();
            setupFilterToggle();
        }
    }

    initMobileFeatures();

    // d) Window resize handler
    window.addEventListener('resize', function() {
        if (window.innerWidth >= 768) {
            document.body.classList.remove('mobile-nav-open');
            const filter = document.getElementById('changelist-filter');
            if (filter) filter.classList.remove('filter-open');
        } else {
            // Re-setup if needed
            setupSidebarToggle();
            setupFilterToggle();
            injectDataLabels();
        }
    });
});
