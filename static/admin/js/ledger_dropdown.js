// Ledger download dropdown — fixed positioning to escape table overflow:hidden
function svedToggleDrop(btn, menuId) {
    var menu = document.getElementById(menuId);
    var isOpen = menu.style.display === 'block';

    // close every open sved dropdown
    document.querySelectorAll('.sved-ddmenu').forEach(function (el) {
        el.style.display = 'none';
    });

    if (!isOpen) {
        var rect = btn.getBoundingClientRect();
        menu.style.top  = rect.bottom + 'px';
        menu.style.left = rect.left + 'px';
        menu.style.display = 'block';
    }
}

document.addEventListener('click', function (e) {
    if (!e.target.closest('[data-sved-toggle]')) {
        document.querySelectorAll('.sved-ddmenu').forEach(function (el) {
            el.style.display = 'none';
        });
    }
});
