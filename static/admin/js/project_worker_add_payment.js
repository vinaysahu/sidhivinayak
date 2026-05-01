/**
 * Add-Payment modal for the Project Workers inline on the Project change
 * page. Triggered by buttons rendered by ProjectWorkersInline.add_payment_action.
 */
(function () {
    'use strict';

    function getCookie(name) {
        const match = document.cookie.split('; ').find(r => r.startsWith(name + '='));
        return match ? match.split('=')[1] : '';
    }

    function buildModal() {
        if (document.getElementById('apw-modal')) return;

        const wrap = document.createElement('div');
        wrap.id = 'apw-modal';
        wrap.style.cssText =
            'display:none;position:fixed;top:0;left:0;width:100%;height:100%;' +
            'background:rgba(0,0,0,0.55);z-index:99999;align-items:center;' +
            'justify-content:center;';
        wrap.innerHTML =
            '<div style="background:#fff;padding:22px 24px;border-radius:8px;' +
            'width:420px;max-width:92%;box-shadow:0 8px 24px rgba(0,0,0,0.2);' +
            'font-family:-apple-system,Segoe UI,Roboto,sans-serif;">' +
                '<h3 style="margin:0 0 14px 0;font-size:16px;color:#222;">Add Payment</h3>' +
                '<p id="apw-worker" style="margin:0 0 4px 0;font-size:13px;color:#444;"></p>' +
                '<p style="margin:0 0 14px 0;font-size:13px;color:#666;">' +
                    'Outstanding Balance: <strong id="apw-balance" style="color:#c0392b;"></strong>' +
                '</p>' +
                '<label style="display:block;font-size:13px;font-weight:600;color:#333;">Amount (₹)</label>' +
                '<input type="number" id="apw-amount" step="0.01" min="0" ' +
                    'style="width:100%;padding:8px 10px;border:1px solid #ccc;' +
                    'border-radius:4px;margin-top:4px;font-size:14px;" placeholder="0">' +
                '<p id="apw-error" style="color:#c0392b;font-size:12px;' +
                    'margin:8px 0 0 0;display:none;"></p>' +
                '<div style="margin-top:18px;text-align:right;">' +
                    '<button type="button" id="apw-cancel" ' +
                        'style="padding:7px 14px;margin-right:8px;background:#aaa;' +
                        'color:#fff;border:none;border-radius:4px;cursor:pointer;' +
                        'font-size:13px;">Cancel</button>' +
                    '<button type="button" id="apw-save" ' +
                        'style="padding:7px 16px;background:#27ae60;color:#fff;' +
                        'border:none;border-radius:4px;cursor:pointer;font-size:13px;' +
                        'font-weight:600;">Save Payment</button>' +
                '</div>' +
            '</div>';
        document.body.appendChild(wrap);
    }

    let currentUrl = null;
    let currentBalance = 0;

    function showModal(url, balance, worker) {
        buildModal();
        currentUrl = url;
        currentBalance = parseFloat(balance);
        document.getElementById('apw-worker').textContent = 'Worker: ' + worker;
        document.getElementById('apw-balance').textContent =
            '₹' + currentBalance.toFixed(2);
        const amt = document.getElementById('apw-amount');
        amt.value = '';
        amt.max = String(currentBalance);
        document.getElementById('apw-error').style.display = 'none';
        const save = document.getElementById('apw-save');
        save.disabled = false;
        save.textContent = 'Save Payment';
        document.getElementById('apw-modal').style.display = 'flex';
        amt.focus();
    }

    function hideModal() {
        const m = document.getElementById('apw-modal');
        if (m) m.style.display = 'none';
        currentUrl = null;
    }

    function showError(msg) {
        const e = document.getElementById('apw-error');
        e.textContent = msg;
        e.style.display = 'block';
    }

    async function submitPayment() {
        const amt = parseFloat(document.getElementById('apw-amount').value);
        if (isNaN(amt) || amt <= 0) {
            showError('Valid amount daalo');
            return;
        }
        if (amt > currentBalance) {
            showError('Amount ₹' + amt + ' balance ₹' +
                currentBalance.toFixed(2) + ' se zyada nahi ho sakta');
            return;
        }

        const save = document.getElementById('apw-save');
        save.disabled = true;
        save.textContent = 'Saving...';

        try {
            const res = await fetch(currentUrl, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify({ amount: amt }),
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) {
                showError(data.error || ('Save failed (HTTP ' + res.status + ')'));
                save.disabled = false;
                save.textContent = 'Save Payment';
                return;
            }
            alert(data.message || 'Payment saved');
            hideModal();
            window.location.reload();
        } catch (err) {
            showError('Network error: ' + err.message);
            save.disabled = false;
            save.textContent = 'Save Payment';
        }
    }

    function bindOnce() {
        if (document.body.dataset.apwBound === '1') return;
        document.body.dataset.apwBound = '1';

        // Event delegation: catches clicks on .add-payment-btn no matter
        // when (or how) the inline rows are rendered.
        document.body.addEventListener('click', function (e) {
            const btn = e.target.closest('.add-payment-btn');
            if (btn) {
                e.preventDefault();
                showModal(
                    btn.dataset.url,
                    btn.dataset.balance,
                    btn.dataset.worker
                );
                return;
            }
            if (e.target.id === 'apw-cancel') {
                hideModal();
                return;
            }
            if (e.target.id === 'apw-save') {
                submitPayment();
                return;
            }
            if (e.target.id === 'apw-modal') {
                hideModal();
            }
        });

        document.addEventListener('keydown', function (e) {
            const m = document.getElementById('apw-modal');
            if (!m || m.style.display === 'none') return;
            if (e.key === 'Escape') {
                hideModal();
            } else if (e.key === 'Enter' && document.activeElement &&
                document.activeElement.id === 'apw-amount') {
                e.preventDefault();
                submitPayment();
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bindOnce);
    } else {
        bindOnce();
    }
})();

// Per-Sq-Ft area toggle + live total for ProjectWorkers inline
(function () {
    'use strict';

    var PER_SQ_FT = '30';

    function updateAreaCell(row, wagesTypeValue) {
        var areaCell = row.querySelector('.field-area');
        if (!areaCell) return;
        var areaInput = areaCell.querySelector('input');

        if (wagesTypeValue === PER_SQ_FT) {
            areaCell.style.opacity = '1';
            if (areaInput) {
                areaInput.disabled = false;
                areaInput.style.border = '2px solid #e74c3c';
                areaInput.style.background = '';
                areaInput.placeholder = 'Required';
            }
        } else {
            areaCell.style.opacity = '0.35';
            if (areaInput) {
                areaInput.disabled = true;
                areaInput.value = '';
                areaInput.style.border = '';
                areaInput.style.background = '#f0f0f0';
                areaInput.placeholder = '';
            }
        }
    }

    function updateTotal(row) {
        var wagesTypeSelect = row.querySelector('.field-wages_type select');
        var wagesInput = row.querySelector('.field-wages input');
        var areaInput = row.querySelector('.field-area input');
        var totalCell = row.querySelector('.field-total_payment_display');
        if (!totalCell) return;

        var totalSpan = totalCell.querySelector('.pw-total-display');
        if (!totalSpan) {
            totalSpan = document.createElement('span');
            totalSpan.className = 'pw-total-display';
            totalCell.innerHTML = '';
            totalCell.appendChild(totalSpan);
        }

        if (wagesTypeSelect && wagesTypeSelect.value === PER_SQ_FT && wagesInput && areaInput) {
            var wages = parseFloat(wagesInput.value) || 0;
            var area = parseFloat(areaInput.value) || 0;
            if (wages > 0 && area > 0) {
                var total = wages * area;
                totalSpan.textContent = '₹' + total.toFixed(2);
                totalSpan.style.color = '#27ae60';
                totalSpan.style.fontWeight = 'bold';
            } else {
                totalSpan.textContent = '—';
                totalSpan.style.color = '';
                totalSpan.style.fontWeight = '';
            }
        } else {
            totalSpan.textContent = '—';
            totalSpan.style.color = '';
            totalSpan.style.fontWeight = '';
        }
    }

    function initRow(row) {
        var wagesTypeSelect = row.querySelector('.field-wages_type select');
        if (!wagesTypeSelect) return;
        if (row.dataset.pwInited) return;
        row.dataset.pwInited = '1';

        updateAreaCell(row, wagesTypeSelect.value);
        updateTotal(row);

        wagesTypeSelect.addEventListener('change', function () {
            updateAreaCell(row, this.value);
            updateTotal(row);
        });

        var wagesInput = row.querySelector('.field-wages input');
        if (wagesInput) {
            wagesInput.addEventListener('input', function () { updateTotal(row); });
        }

        var areaInput = row.querySelector('.field-area input');
        if (areaInput) {
            areaInput.addEventListener('input', function () { updateTotal(row); });
        }
    }

    function initAllRows() {
        var inlineGroup = document.querySelector('#projectworkers_set-group');
        if (!inlineGroup) return;
        var rows = inlineGroup.querySelectorAll('tr');
        for (var i = 0; i < rows.length; i++) {
            initRow(rows[i]);
        }
    }

    // Handle "Add another" rows
    document.addEventListener('formset:added', function (e) {
        var row = e.target;
        if (row) initRow(row);
    });

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAllRows);
    } else {
        initAllRows();
    }
})();
