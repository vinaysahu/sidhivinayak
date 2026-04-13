document.addEventListener('DOMContentLoaded', function () {

    function formatNumber(value) {
        if (value === null || value === undefined || value === '') return '₹ 0.00';

        let number = parseFloat(value.toString().replace(/,/g, '').trim());

        if (isNaN(number)) return '₹ 0.00';

        // Indian numbering system logic
        let parts = number.toFixed(2).split('.');
        let integerPart = parts[0];
        let decimalPart = parts[1];
        
        let lastThree = integerPart.slice(-3);
        let otherParts = integerPart.slice(0, -3);
        
        if (otherParts !== '' && otherParts !== '-') {
            let prefix = "";
            if (otherParts.startsWith("-")) {
                prefix = "-";
                otherParts = otherParts.substring(1);
            }
            otherParts = otherParts.split('').reverse().join('');
            let groups = [];
            for (let i = 0; i < otherParts.length; i += 2) {
                groups.push(otherParts.substring(i, i + 2));
            }
            otherParts = groups.join(',').split('').reverse().join('');
            integerPart = prefix + otherParts + ',' + lastThree;
        }

        return `₹ ${integerPart}.${decimalPart}`;
    }

    function numberToWords(num) {
        if (!num || isNaN(parseFloat(num)) || parseFloat(num) === 0) return 'Zero';

        const a = ["","One","Two","Three","Four","Five","Six","Seven","Eight","Nine","Ten",
        "Eleven","Twelve","Thirteen","Fourteen","Fifteen","Sixteen","Seventeen",
        "Eighteen","Nineteen"];
        const b = ["","","Twenty","Thirty","Forty","Fifty","Sixty","Seventy","Eighty","Ninety"];

        function inWords(n) {
            n = Math.abs(parseInt(n));
            if (n < 20) return a[n];
            if (n < 100) return b[Math.floor(n/10)] + (n%10 !== 0 ? " " + a[n%10] : "");
            if (n < 1000) return a[Math.floor(n/100)] + " Hundred" + (n%100 !== 0 ? " and " + inWords(n%100) : "");
            if (n < 100000) return inWords(Math.floor(n/1000)) + " Thousand" + (n%1000 !== 0 ? " " + inWords(n%1000) : "");
            if (n < 10000000) return inWords(Math.floor(n/100000)) + " Lakh" + (n%100000 !== 0 ? " " + inWords(n%100000) : "");
            return inWords(Math.floor(n/10000000)) + " Crore" + (n%10000000 !== 0 ? " " + inWords(n%10000000) : "");
        }

        return inWords(num);
    }

    function updateLiveSummary(value) {
        const cleanValue = value.replace(/,/g, '');
        const formatted = formatNumber(cleanValue);
        const words = numberToWords(cleanValue) + " Rupees Only";
        
        document.querySelectorAll('.live-amount').forEach(el => {
            el.innerText = formatted;
        });
        document.querySelectorAll('.live-amount-words').forEach(el => {
            el.innerText = words;
        });
    }

    function attachPreview(fieldId) {
        const input = document.getElementById(fieldId);
        if (!input) return;

        // 👇 formatted preview div (for the field itself)
        let preview = input.parentNode.querySelector('.amt-preview');
        if (!preview) {
            preview = document.createElement('div');
            preview.className = 'amt-preview';
            preview.style.marginTop = '5px';
            preview.style.fontWeight = 'bold';
            preview.style.color = '#2e7d32';
            input.parentNode.appendChild(preview);
        }

        // 👇 words preview div
        let wordsDiv = input.parentNode.querySelector('.words-preview');
        if (!wordsDiv) {
            wordsDiv = document.createElement('div');
            wordsDiv.className = 'words-preview';
            wordsDiv.style.fontSize = '12px';
            wordsDiv.style.color = '#555';
            input.parentNode.appendChild(wordsDiv);
        }

        function updatePreview() {
            let value = input.value;
            let clean = value.replace(/,/g, '');
            
            preview.innerText = formatNumber(clean);
            wordsDiv.innerText = numberToWords(clean) + " Rupees Only";
            
            // Also update the UPAR/NICHE summary blocks if we are on id_amount
            if (fieldId === 'id_amount') {
                updateLiveSummary(clean);
            }
        }

        input.addEventListener('input', updatePreview);
        updatePreview();
    }

    // Attach to primary amount fields
    attachPreview('id_amount');
    attachPreview('id_balance');

    // Handle existing readonly elements (like in list view or other admin pages)
    const readonlySelectors = [
        '.field-amount .readonly', 
        '.field-balance .readonly',
        '.field-amount_display .readonly',
        '.field-paid_amount_display .readonly',
        '.field-balance_display .readonly'
    ];
    
    document.querySelectorAll(readonlySelectors.join(',')).forEach(function (el) {
        let rawValue = el.innerText.replace(/[₹,]/g, '').trim();
        if (!rawValue || isNaN(parseFloat(rawValue))) return;
        
        el.innerHTML = `
            <span style="color: #2e7d32; font-weight: bold;">${formatNumber(rawValue)}</span>
            <br>
            <small style="color: #666;">(${numberToWords(rawValue)} Rupees Only)</small>
        `;
    });

});