document.addEventListener("DOMContentLoaded", function () {
  const nameInput = document.getElementById("id_name");
  const skuInput = document.getElementById("id_sku");

  if (nameInput && skuInput) {
    nameInput.addEventListener("input", function () {
      let nameValue = nameInput.value
        .trim()
        .toLowerCase()
        .replace(/\s+/g, "_") // spaces → underscore
        .replace(/[^a-z0-9_]/g, ""); // remove special chars

      skuInput.value = nameValue;
    });
  }
});
