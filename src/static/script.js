// Get DOM elements
const uploadForm = document.getElementById("upload-form");
const fileInputContainer = document.getElementById("file-input-container");
const addFileButton = document.getElementById("add-file-button");
const progressContainer = document.getElementById("progress-container");
const progressBar = document.getElementById("progress-bar");
const linkContainer = document.getElementById("link-container");
const fileInput = document.getElementById('file-upload');
const fileSizeWarning = document.getElementById('file-size-warning');

// Keep track of selected file names to detect duplicates
const selectedFileNames = new Set();

// Max file size limit (in bytes)
const MAX_FILE_SIZE_GUEST = 20 * 1024 * 1024; // 20 MB
const MAX_FILE_SIZE_USER = 200 * 1024 * 1024; // 200 MB
let isLoggedIn = false;

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

function addAnotherFile() {
    const newFileInput = document.createElement("input");
    newFileInput.type = "file";
    newFileInput.name = "files";
    newFileInput.className = "form-control mb-3"; // Add Bootstrap class
    newFileInput.required = true;
    newFileInput.multiple = true;

    // Check for duplicate files
    newFileInput.addEventListener("change", (event) => checkForDuplicate(event.target));
    fileInputContainer.appendChild(newFileInput);
}

function fileInputHandler() {
    const files = fileInput.files;
    let isValid = true;
    const fileSizeLimit = isLoggedIn ? MAX_FILE_SIZE_USER : MAX_FILE_SIZE_GUEST;

    // Check each file's size
    for (let i = 0; i < files.length; i++) {
        if (files[i].size > fileSizeLimit) {
            isValid = false;
            break;
        }
    }

    if (isValid) {
        fileSizeWarning.style.display = 'none'; // Hide warning if files are valid
    } else {
        fileSizeWarning.style.display = 'block'; // Show warning if a file exceeds size limit
    }
}

function handleSubmit(event) {
    event.preventDefault();

    const fileInputs = document.querySelectorAll('input[type="file"]');
    const formData = new FormData();
    const submittedFiles = new Set();
    const fileSizeLimit = isLoggedIn ? MAX_FILE_SIZE_USER : MAX_FILE_SIZE_GUEST;

    let fileSelected = false;

    for (let input of fileInputs) {
        const fileList = input.files;

        if (fileList.length > 0) {
            fileSelected = true;
            for (let file of fileList) {
                // Make sure file size does not exceed limit
                if (file.size > fileSizeLimit) {
                    fileSizeWarning.style.display = 'block';
                    return;
                }
                else if (!submittedFiles.has(file.name)) {
                    formData.append("files", file);
                    submittedFiles.add(file.name);
                }
            }
        }
    }

    if (!fileSelected) {
        linkContainer.innerHTML = `<div class="text-danger">Please select at least one file.</div>`;
        return;
    }

    // Show progress bar
    progressContainer.style.display = "block";

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/files/");

    // Update progress bar during upload
    xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
            const percentComplete = Math.round((event.loaded / event.total) * 100);
            progressBar.style.width = `${percentComplete}%`;
            progressBar.textContent = `${percentComplete}%`;
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
                <div class="alert alert-success">
                    <p>Files uploaded successfully! Access them here:</p>
                    <a href="${fileLink}" target="_blank" class="btn btn-link">${fileLink}</a>
                    <button class="btn btn-primary btn-sm copy-button" onclick="copyLink('${fileLink}')">Copy Link</button>
                </div>
            `;
        } else {
            progressContainer.style.display = "none";
            linkContainer.innerHTML = `<div class="text-danger">An error occurred while uploading. Please try again.</div>`;
            console.error("Upload error:", xhr.responseText);
        }
    };

    // Handle errors
    xhr.onerror = () => {
        progressContainer.style.display = "none";
        linkContainer.innerHTML = `<div class="text-danger">An error occurred during the upload.</div>`;
        console.error("Upload error:", xhr.responseText);
    };

    // Send the form data
    xhr.send(formData);
}

// Copy to clipboard function
function copyLink(fileLink) {
    navigator.clipboard
        .writeText(fileLink)
        .then(() => alert("Link copied to clipboard!"))
        .catch((error) => console.error("Failed to copy link:", error));
}

// Function to check if the user is logged in by checking the presence of the JWT token
function checkLoginStatus() {
    const token = document.cookie.split('; ').find(row => row.startsWith('access_token='));
    isLoggedIn = token !== undefined;

    if (isLoggedIn) {
        document.getElementById('login-btn').style.display = 'none';
        document.getElementById('logout-btn').style.display = 'inline-block';
    } else {
        document.getElementById('login-btn').style.display = 'inline-block';
        document.getElementById('logout-btn').style.display = 'none';
    }
}

function logout() {
    document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/';
    window.location.href = '/';  // Redirect to the home page after logging out
}


// Function to format date as a string (e.g., "January 1, 2024")
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
    });
}

function addFilesToList(files) {
    const fileListContainer = document.getElementById('file-list');
    const linkContainer = document.getElementById('link-container')

    // Make sure the list is visible
    linkContainer.classList.remove('d-none');

    // Group files by date
    const groupedFiles = files.reduce((groups, fileData) => {
        const date = formatDate(fileData.uploaded_at);
        if (!groups[date]) {
            groups[date] = [];
        }
        groups[date].push(fileData);
        return groups;
    }, {});

    // Create HTML structure for each group
    for (const [date, filesOnDate] of Object.entries(groupedFiles)) {
        const groupContainer = document.createElement('div');
        const groupHeader = document.createElement('h4');
        groupHeader.textContent = date;
        groupContainer.appendChild(groupHeader);

        const listGroup = document.createElement('ul');
        listGroup.classList.add('list-group');

        // Create a list item for each file
        filesOnDate.forEach(fileData => {
            const listItem = document.createElement('li');
            listItem.classList.add('list-group-item');
            listItem.classList.add('d-flex', 'justify-content-between', 'align-items-center'); // Flex layout to align content

            const fileLink = document.createElement('a');
            fileLink.href = `/files/serve/${fileData.file_id}`;
            fileLink.textContent = `${fileData.filename}`;
            fileLink.classList.add('text-decoration-none');

            const timestampText = document.createElement('p');
            timestampText.textContent = `Uploaded at: ${new Date(fileData.uploaded_at).toLocaleString()}`;

            // Create a Delete button for each file, positioned to the right
            const deleteButton = document.createElement('button');
            deleteButton.classList.add('btn', 'btn-danger', 'btn-sm');
            deleteButton.textContent = 'Delete';
            deleteButton.addEventListener('click', function() {
                // Remove the list item from the view
                listGroup.removeChild(listItem);
                removeFile(fileData.file_id);
            });

            // Append file link, timestamp, and delete button to list item
            listItem.appendChild(fileLink);
            listItem.appendChild(timestampText);
            listItem.appendChild(deleteButton);

            // Add list item to the list group
            listGroup.appendChild(listItem);
        });

        // Add the list group to the group container
        groupContainer.appendChild(listGroup);

        // Append the group container to the main file list container
        fileListContainer.appendChild(groupContainer);
    }
}

// Function to display the files as a grouped list by date
function displayFileList() {
    if (isLoggedIn) {
        fetch('/files/list', {
            method: 'GET',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(responseData => {
            data = responseData;
            if (data.length) {
                addFilesToList(data);
            }
        })
        .catch(error => console.error('Error:', error));
    } else {
        console.log("User is not logged in.");
        return;
    }
    console.log("User is logged in: ", isLoggedIn);
}

function removeFile(fileId) {
    fetch(`/files/${fileId}`, {
        method: 'DELETE',
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(responseData => {
        console.log(responseData);
    })
    .catch(error => console.error('Error:', error));
}

// Display the file list when the page loads
window.onload = function() {
    // Make sure this is called before using any function that requires login status
    checkLoginStatus();
    displayFileList();

    // Attach event listeners
    // Log out user (clear the cookie)
    document.getElementById('logout-btn')?.addEventListener('click', logout);
    // Handle form submission with progress bar
    uploadForm.addEventListener("submit", handleSubmit);
    // Event listener to check file size when a file is selected
    fileInput.addEventListener('change', fileInputHandler);
    // Add event listener to "Add Another File" button
    addFileButton.addEventListener("click", addAnotherFile);

};