// Get DOM elements
const form = document.getElementById("upload-form");
const fileInputContainer = document.getElementById("file-input-container");
const addFileButton = document.getElementById("add-file-button");
const progressContainer = document.getElementById("progress-container");
const progressBar = document.getElementById("progress-bar");
const progressText = document.getElementById("progress-text");
const linkContainer = document.getElementById("link-container");

// Keep track of selected file names to detect duplicates
const selectedFileNames = new Set();

// Add event listener to "Add Another File" button
addFileButton.addEventListener("click", () => {
    const newFileInput = document.createElement("input");
    newFileInput.type = "file";
    newFileInput.name = "files";
    newFileInput.required = true;

    // Check for duplicate files
    newFileInput.addEventListener("change", (event) => checkForDuplicate(event.target));
    fileInputContainer.appendChild(newFileInput);
});

function checkForDuplicate(input) {
    const fileList = input.files;
    if (!fileList || fileList.length === 0) return;

    const duplicateFiles = [];

    for (let file of fileList) {
        if (selectedFileNames.has(file.name)) {
            duplicateFiles.push(file.name);
        } else {
            selectedFileNames.add(file.name);
        }
    }

    if (duplicateFiles.length > 0) {
        alert(`Duplicate file(s) detected: ${duplicateFiles.join(", ")}. Please select unique files.`);
        input.value = ""; // Clear the problematic input
    }
}

// Handle form submission with progress bar
form.addEventListener("submit", (event) => {
    event.preventDefault();

    const fileInputs = document.querySelectorAll('input[type="file"]');
    const formData = new FormData();
    const submittedFiles = new Set();

    let fileSelected = false;

    for (let input of fileInputs) {
        const fileList = input.files;

        if (fileList.length > 0) {
            fileSelected = true;
            for (let file of fileList) {
                if (!submittedFiles.has(file.name)) {
                    formData.append("files", file);
                    submittedFiles.add(file.name);
                }
            }
        }
    }

    if (!fileSelected) {
        linkContainer.textContent = "Please select at least one file.";
        return;
    }

    // Show progress bar
    progressContainer.style.display = "block";

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/upload/");

    // Update progress bar during upload
    xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
            const percentComplete = Math.round((event.loaded / event.total) * 100);
            progressBar.value = percentComplete;
            progressText.textContent = `${percentComplete}%`;
        }
    };

    // Handle response when upload is complete
    xhr.onload = () => {
        if (xhr.status === 200) {
            const response = JSON.parse(xhr.responseText);
            const { file_link } = response;

            // Hide progress bar after upload
            progressContainer.style.display = "none";

            // Display the link
            const fileLink = `${window.location.origin}${file_link}`;
            linkContainer.innerHTML = `
                <p>Files uploaded successfully! Access them here:</p>
                <a href="${fileLink}" target="_blank">${fileLink}</a>
                <br />
                <button class="copy-button" onclick="copyLink('${fileLink}')">Copy Link</button>
            `;
        } else {
            progressContainer.style.display = "none";
            linkContainer.textContent = "An error occurred while uploading.";
            console.error("Upload error:", xhr.responseText);
        }
    };

    // Handle errors
    xhr.onerror = () => {
        progressContainer.style.display = "none";
        linkContainer.textContent = "An error occurred during the upload.";
        console.error("Upload error:", xhr.responseText);
    };

    // Send the form data
    xhr.send(formData);
});

// Copy to clipboard function
function copyLink(fileLink) {
    navigator.clipboard
        .writeText(fileLink)
        .then(() => alert("Link copied to clipboard!"))
        .catch((error) => console.error("Failed to copy link:", error));
}