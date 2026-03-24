document.addEventListener('DOMContentLoaded', function () {

    function formatNumber(value) {
        if (value === null || value === undefined) return '';

        let number = parseFloat(value.toString().replace(/,/g, '').trim());

        if (isNaN(number)) return '';

        let isInteger = Number.isInteger(number);

        let formatted = number.toLocaleString('en-IN', {
            minimumFractionDigits: isInteger ? 0 : 2,
            maximumFractionDigits: 2
        });

        return `₹ ${formatted}`;
    }

    // 👇 Number to words (simple version)
    function numberToWords(num) {
        if (!num) return '';

        const a = ["","One","Two","Three","Four","Five","Six","Seven","Eight","Nine","Ten",
        "Eleven","Twelve","Thirteen","Fourteen","Fifteen","Sixteen","Seventeen",
        "Eighteen","Nineteen"];
        const b = ["","","Twenty","Thirty","Forty","Fifty","Sixty","Seventy","Eighty","Ninety"];

        function inWords(n) {
            if (n < 20) return a[n];
            if (n < 100) return b[Math.floor(n/10)] + " " + a[n%10];
            if (n < 1000) return a[Math.floor(n/100)] + " Hundred " + inWords(n%100);
            if (n < 100000) return inWords(Math.floor(n/1000)) + " Thousand " + inWords(n%1000);
            if (n < 10000000) return inWords(Math.floor(n/100000)) + " Lakh " + inWords(n%100000);
            return inWords(Math.floor(n/10000000)) + " Crore " + inWords(n%10000000);
        }

        return inWords(parseInt(num)) ;  // + " Rupees"
    }

    function attachPreview(fieldId) {
        const input = document.getElementById(fieldId);
        if (!input) return;

        // 👇 formatted preview
        const preview = document.createElement('div');
        preview.style.marginTop = '5px';
        preview.style.fontWeight = 'bold';
        preview.style.color = '#2e7d32';

        // 👇 words preview
        const words = document.createElement('div');
        words.style.fontSize = '12px';
        words.style.color = '#555';

        input.parentNode.appendChild(preview);
        input.parentNode.appendChild(words);

        function updatePreview() {
            let value = input.value;
            if (!value) {
                preview.innerText = '';
                words.innerText = '';
                return;
            }

            let clean = value.replace(/,/g, '');
            preview.innerText =  formatNumber(clean); //"₹ " +
            words.innerText = numberToWords(clean);
        }

        // 👇 typing pe update
        input.addEventListener('input', updatePreview);

        // 👇 page load pe bhi run hoga
        updatePreview();
    }

    attachPreview('id_amount');
    attachPreview('id_balance');

    const elements = document.querySelectorAll('.field-amount .readonly, .field-balance .readonly');
    const inlineElements = document.querySelectorAll('.field-amount p');

    elements.forEach(function (el) {
        let rawValue = el.innerText;

        if (!rawValue) return;

        el.innerHTML = `
        ${formatNumber(rawValue)}
            <br>
            <small>
                (${numberToWords(rawValue)})
            </small>
        `;
    });

    inlineElements.forEach(function (el) {
        let rawValue = el.innerText;

        if (!rawValue) return;

        el.innerHTML = `
        ${formatNumber(rawValue)}
            <br>
            <small>
                (${numberToWords(rawValue)})
            </small>
        `;
    });

});