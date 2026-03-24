document.addEventListener("click", function(e) {
    if (e.target.matches(".extract-bill-btn")) {
    e.preventDefault();

    const fileInput = document.getElementById("id_bill_image");

    if (!fileInput.files.length) {
        alert("Please select image first");
        return;
    }

    const formData = new FormData();
    formData.append("image", fileInput.files[0]);

    fetch("/admin/projects/projectmaterials/extract-bill-from-image/", {
        method: "POST",
        body: formData,
        headers: {
            "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {

        if (data.error) {
            alert(data.error);
            return;
        }
        console.log("data data data data data data:",data)

        alert(data);
    });
    }
});
