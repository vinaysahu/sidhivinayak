document.addEventListener("DOMContentLoaded", function () {
  const saveBtn = document.getElementById("saveChildProducts");
  if (!saveBtn) return;

  saveBtn.addEventListener("click", function () {
    const rows = document.querySelectorAll("#childProductsTable tbody tr");
    const data = [];

    rows.forEach((row) => {
      const id = row.getAttribute("data-id");
      const qty = row.querySelector(".child-qty").value;
      const price = row.querySelector(".child-price").value;
      data.push({ id, quantity: qty, price });
    });

    fetch("/admin/productManagement/products/update_child_products/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCSRFToken(),
      },
      body: JSON.stringify(data),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "success") {
          alert("Child products updated successfully!");
        } else {
          alert("Failed to update.");
        }
      })
      .catch(() => alert("Something went wrong."));
  });

  function getCSRFToken() {
    const name = "csrftoken";
    const cookies = document.cookie.split(";");
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + "=")) {
        return decodeURIComponent(cookie.substring(name.length + 1));
      }
    }
    return "";
  }
});
