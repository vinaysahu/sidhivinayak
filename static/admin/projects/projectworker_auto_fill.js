document.addEventListener("DOMContentLoaded", function () {


    // Django ka inline add button class
    // ".add-row" tabular inline ke add button ka container hota hai
    document.body.addEventListener('click', function (e) {
        addRow = e.target.closest('.add-row')
        if (e.target.closest('.add-row') && e.target.tagName === "A") {
            const lastRow = addRow.previousElementSibling;
            const secondLastRow = lastRow ? lastRow.previousElementSibling : null;
            console.log("vsds","#id_"+secondLastRow.id+"-worker_id");

    $("#id_"+secondLastRow.id+"-worker_id").change(()=>{
            
            let workerId = $("#id_"+secondLastRow.id+"-worker_id").val();
            console.log("this.val()",workerId)

            if (!workerId) return;

            fetch(`/projects/get-worker-wages/?worker_id=${workerId}`)
                .then(response => response.json())
                .then(data => {
                    let wagesFieldId = "id_"+secondLastRow.id+"-wages";
                    let wagesField = document.getElementById(wagesFieldId);
                    if (wagesField) {
                        wagesField.value = data.wages;  // Auto-fill
                    }

                    let typeFieldId = "id_"+secondLastRow.id+"-wages_type";
                    let typeField = document.getElementById(typeFieldId);
                    if (typeField) {
                        typeField.value = data.type;  // Auto-fill
                    }
                });
        });
        }
    });

    // All inline worker dropdowns
    // document.querySelectorAll("select[name^='projectworkers_set-'][name$='-worker_id']").forEach(function (selectEl) {

    //     console.log("thselectElis",selectEl.id)
    //     console.log("this",this)

    //     $("#"+selectEl.id).change(()=>{
    //         // console.log("this.val()",selectEl.value)
    //         let workerId = selectEl.value;

    //         if (!workerId) return;

    //         fetch(`/projects/get-worker-wages/?worker_id=${workerId}`)
    //             .then(response => response.json())
    //             .then(data => {
    //                 let wagesFieldId = selectEl.id.replace("worker_id", "wages");
    //                 let wagesField = document.getElementById(wagesFieldId);
    //                 if (wagesField) {
    //                     wagesField.value = data.wages;  // Auto-fill
    //                 }

    //                 let typeFieldId = selectEl.id.replace("worker_id", "wages_type");
    //                 let typeField = document.getElementById(typeFieldId);
    //                 if (typeField) {
    //                     typeField.value = data.type;  // Auto-fill
    //                 }
    //             });
    //     });
        
        // selectEl.addEventListener("change", function () {
        //     let workerId = this.value;
        //     alert(workerId)

        //     if (!workerId) return;

            

        //     // Fetch wages from your custom Django API endpoint
        //     fetch(`/admin/projects/get-worker-wages/?worker_id=${workerId}`)
        //         .then(response => response.json())
        //         .then(data => {
        //             let wagesFieldId = this.id.replace("worker_id", "wages");
        //             let wagesField = document.getElementById(wagesFieldId);
        //             if (wagesField) {
        //                 wagesField.value = data.wages;  // Auto-fill
        //             }
        //         });
        // });
    // });
});
