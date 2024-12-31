// Extract 'unique_id' from the URL path
const pathParts = window.location.pathname.split("/");
const uniqueId = pathParts[pathParts.length - 1]; // Get the last part of the URL (e.g., /files/<unique_id>)

const fileListContainer = document.getElementById("file-list-container");
const statusMessage = document.getElementById("status-message");

if (!uniqueId) {
    // If no 'id' parameter is present in the URL, show an error
    statusMessage.textContent = "Invalid or missing link. Please use a valid shared link.";
} else {
    // Fetch the files associated with the unique_id
    fetch(`/files-json/${uniqueId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error fetching files: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            // Check if files exist in the response
            if (data.files && data.files.length > 0) {
                // Hide the status message
                statusMessage.style.display = "none";

                // Create a list to display the files
                const fileList = document.createElement("ul");
                fileList.classList.add("file-list");

                // Iterate over each file object in the response
                data.files.forEach(file => {
                    // Create a list item for each file
                    const listItem = document.createElement("li");
                    listItem.classList.add("file-item");

                    // Create an anchor tag for downloading the file
                    const fileLink = document.createElement("a");
                    fileLink.href = file.download_link; // Use the provided download link
                    fileLink.textContent = file.filename; // Display the file name
                    fileLink.target = "_blank"; // Open the link in a new tab

                    // Append the anchor tag to the list item
                    listItem.appendChild(fileLink);

                    // Append the list item to the file list
                    fileList.appendChild(listItem);
                });

                // Append the rendered file list to the container
                fileListContainer.appendChild(fileList);
            } else {
                // No files were found for this ID
                statusMessage.textContent = "No files found for this link.";
            }
        })
        .catch(error => {
            console.error("Error loading files:", error);
            statusMessage.textContent = "Failed to load files. Please try again later.";
        });
}