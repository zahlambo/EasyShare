// Get DOM elements
   const form = document.getElementById("upload-form");
   const fileInputContainer = document.getElementById("file-input-container");
   const addFileButton = document.getElementById("add-file-button");
   const progressContainer = document.getElementById("progress-container");
   const progressBar = document.getElementById("progress-bar");
   const linkContainer = document.getElementById("link-container");

   // Keep track of selected file names to detect duplicates
   const selectedFileNames = new Set();

   // Add event listener to "Add Another File" button
   addFileButton.addEventListener("click", () => {
       const fileInputWrapper = document.createElement("div");
       fileInputWrapper.className = "file-input-wrapper";

       const newFileInput = document.createElement("input");
       newFileInput.type = "file";
       newFileInput.name = "files";
       newFileInput.className = "form-control mb-3"; // Add Bootstrap class
       newFileInput.required = true;
       newFileInput.multiple = true;

       const removeButton = document.createElement("span");
       removeButton.className = "remove-file-button";
       removeButton.textContent = "Remove";
       removeButton.addEventListener("click", () => {
           fileInputWrapper.remove();
       });

       // Check for duplicate files
       newFileInput.addEventListener("change", (event) => checkForDuplicate(event.target));

       fileInputWrapper.appendChild(newFileInput);
       fileInputWrapper.appendChild(removeButton);
       fileInputContainer.appendChild(fileInputWrapper);
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
           linkContainer.innerHTML = `<div class="text-danger">Please select at least one file.</div>`;
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
   });

   // Copy to clipboard function
   function copyLink(fileLink) {
       navigator.clipboard
           .writeText(fileLink)
           .then(() => alert("Link copied to clipboard!"))
           .catch((error) => console.error("Failed to copy link:", error));
   }