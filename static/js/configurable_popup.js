document.addEventListener("DOMContentLoaded", function () {
  const btn = document.getElementById("generateVariantsBtn");
  if (!btn) return;

  btn.addEventListener("click", function () {
    const pathParts = window.location.pathname.split("/").filter(Boolean);
    const productId = pathParts[pathParts.length - 2];

    fetch(`/admin/productManagement/products/generate_variants/${productId}/`)
      .then((response) => response.json())
      .then((data) => {
        showVariantPopup(data.combinations);
      });
  });
});

function showVariantPopup(combinations) {
  console.log("open variant modal");
  const modal = document.createElement("div");
  modal.classList.add("variant-modal");
  modal.innerHTML = `
        <div class="variant-popup">
            <h3>Generate Variants</h3>
            <form id="variantForm">
                <table class="variant-table">
                    <tr><th>Variant</th><th>Price</th><th>Quantity</th></tr>
                    ${combinations
                      .map(
                        (combo, i) => `
                        <tr>
                            <td>${Object.values(combo).join(" / ")}</td>
                            <td><input type="number" name="price_${i}" step="0.01" value="0"></td>
                            <td><input type="number" name="qty_${i}" value="0"></td>
                        </tr>
                    `
                      )
                      .join("")}
                </table>
                <button type="submit" class="button">Create Variants</button>
                <button type="button" class="button cancel">Cancel</button>
            </form>
        </div>
    `;
  document.body.appendChild(modal);

  modal
    .querySelector(".cancel")
    .addEventListener("click", () => modal.remove());
  modal.querySelector("#variantForm").addEventListener("submit", (e) => {
    e.preventDefault();
    alert("Variants will be created (backend call next step)");
    modal.remove();
  });
}
