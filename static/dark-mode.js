document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.getElementById("darkModeToggle");
    const body = document.body;

    // Add event-based debugging
    toggle.addEventListener("change", () => {
        if (toggle.checked) {
            console.log("Dark mode toggle checked"); // Log toggle checked status
            body.classList.add("dark-mode");
            localStorage.setItem("dark-mode", "enabled");
        } else {
            console.log("Dark mode toggle unchecked"); // Log toggle unchecked status
            body.classList.remove("dark-mode");
            localStorage.setItem("dark-mode", "disabled");
        }
    });

    // Checking saved state in local storage
    if (localStorage.getItem("dark-mode") === "enabled") {
        console.log("Dark mode is enabled from localStorage"); // Debugging log
        body.classList.add("dark-mode");
        toggle.checked = true;
    } else {
        console.log("Dark mode is disabled from localStorage"); // Debugging log
    }
});