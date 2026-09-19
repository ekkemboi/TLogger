(() => {
    const layout = document.querySelector('.app-layout');
    const toggle = document.getElementById('sidebar-toggle');
    const main = document.getElementById('main-content');
    const status = document.getElementById('navigation-status');
    const narrow = matchMedia('(max-width: 700px)');
    let preference;
    try { preference = localStorage.getItem('sidebarCollapsed'); } catch (_) { /* Storage may be disabled. */ }

    function setCollapsed(collapsed, persist = false) {
        layout.classList.toggle('sidebar-collapsed', collapsed);
        toggle.setAttribute('aria-expanded', String(!collapsed));
        toggle.setAttribute('aria-label', collapsed ? 'Expand sidebar' : 'Collapse sidebar');
        toggle.title = toggle.getAttribute('aria-label');
        main.inert = narrow.matches && !collapsed;
        if (persist) {
            preference = String(collapsed);
            try { localStorage.setItem('sidebarCollapsed', preference); } catch (_) { /* Optional preference. */ }
        }
    }
    setCollapsed(narrow.matches || preference === 'true');
    toggle.addEventListener('click', () => setCollapsed(!layout.classList.contains('sidebar-collapsed'), true));
    narrow.addEventListener('change', () => setCollapsed(narrow.matches || preference === 'true'));
    document.querySelector('.sidebar-backdrop').addEventListener('click', () => { setCollapsed(true); toggle.focus(); });
    document.addEventListener('keydown', event => {
        if (event.key === 'Escape' && !layout.classList.contains('sidebar-collapsed')) {
            setCollapsed(true, true);
            toggle.focus();
        }
        if (event.key === 'Tab' && narrow.matches && !layout.classList.contains('sidebar-collapsed')) {
            const items = [...document.querySelectorAll('.sidebar a[href], .sidebar button, .sidebar select')].filter(el => el.getClientRects().length);
            const first = items[0], last = items[items.length - 1];
            if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
            else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
        }
    });
    document.querySelectorAll('.sidebar-link').forEach(link => {
        link.setAttribute('aria-label', link.textContent.trim());
        link.title = link.textContent.trim();
    });
    function updateCurrentPage() {
        document.querySelectorAll('.sidebar-link').forEach(link => {
            const active = link.pathname === location.pathname;
            link.classList.toggle('active', active);
            if (active) link.setAttribute('aria-current', 'page');
            else link.removeAttribute('aria-current');
        });
    }
    updateCurrentPage();
    document.body.addEventListener('htmx:beforeRequest', event => {
        if (event.detail.target !== main) return;
        main.setAttribute('aria-busy', 'true');
        status.textContent = 'Loading page…';
    });
    document.body.addEventListener('htmx:beforeSwap', event => {
        if (event.detail.target === main && event.detail.shouldSwap) {
            window.cleanupDashboard?.();
            main.classList.remove('page-enter');
        }
    });
    document.body.addEventListener('htmx:afterSwap', event => {
        if (event.detail.target !== main) return;
        if (narrow.matches) setCollapsed(true);
        main.classList.add('page-enter');
        const heading = main.querySelector('h1');
        if (heading) {
            document.title = `TradeLogger - ${heading.textContent.trim()}`;
            heading.tabIndex = -1;
            heading.focus({ preventScroll: true });
        }
        updateCurrentPage();
    });
    document.body.addEventListener('htmx:afterRequest', event => {
        if (event.detail.target !== main) return;
        main.removeAttribute('aria-busy');
        status.textContent = event.detail.failed ? 'Unable to load page. Please try again.' : '';
    });
})();
