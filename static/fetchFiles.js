// Extract URL's 'unique_id'
const pathParts = window.location.pathname.split("/");
const uniqueId = pathParts[pathParts.length - 1]; // Last part of the URL (e.g., /files/<unique_id>)

const fileListContainer = document.getElementById("file-list-container");
const statusMessage = document.getElementById("status-message");

if (!uniqueId) {
    // If no 'id' parameter is in URL, show an error
    statusMessage.innerHTML = `<div class="alert alert-danger">Invalid or missing link. Please use a valid shared link.</div>`;
} else {
    // Fetch the files associated with the unique_id
    fetch(`/files/json/${uniqueId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error fetching files: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            // Check if files exist
            if (data.files && data.files.length > 0) {
                statusMessage.style.display = "none";

                // Create a Bootstrap list group
                const fileList = document.createElement("div");
                fileList.classList.add("list-group");

                // Iterate over each file object in the response
                data.files.forEach(file => {
                    const listItem = document.createElement("a");
                    listItem.classList.add("list-group-item", "list-group-item-action"); // Bootstrap classes
                    listItem.href = file.download_link;
                    listItem.textContent = file.filename;
                    listItem.target = "_blank";

                    fileList.appendChild(listItem);
                });

                fileListContainer.appendChild(fileList);
            } else {
                statusMessage.innerHTML = `<div class="alert alert-warning">No files found for this link.</div>`;
            }
        })
        .catch(error => {
            console.error("Error loading files:", error);
            statusMessage.innerHTML = `<div class="alert alert-danger">Failed to load files. Please try again later.</div>`;
        });
}