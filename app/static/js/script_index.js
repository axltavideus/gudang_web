const uploadForm = document.getElementById("uploadForm");
const fileInput = document.getElementById("fileInput");
const downloadLinkDiv = document.getElementById("downloadLink");
const fileLink = document.getElementById("fileLink");
const messageDiv = document.getElementById("message");
const errorDiv = document.getElementById("error");

uploadForm.addEventListener("submit", function(event) {
    event.preventDefault();

    messageDiv.textContent = "";
    errorDiv.textContent = "";
    downloadLinkDiv.style.display = "none";

    if (!fileInput.files[0]) {
        errorDiv.textContent = "Please select a file.";
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    messageDiv.textContent = "Processing file, please wait...";

    fetch("/upload", {
        method: "POST",
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(text => { throw new Error(text) });
        }
        return response.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        fileLink.href = url;
        fileLink.download = fileInput.files[0].name.replace(".xlsx", "_updated.xlsx");
        downloadLinkDiv.style.display = "block";
        messageDiv.textContent = "File processed successfully!";
    })
    .catch(error => {
        errorDiv.textContent = "Error: " + error.message;
        messageDiv.textContent = "";
        console.error("Error:", error);
    });
});
