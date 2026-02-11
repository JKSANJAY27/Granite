document.addEventListener("DOMContentLoaded", () => {
  // Current Page Detection
  const path = window.location.pathname;
  const page = path.split("/").pop();

  // --- Global Navigation Logic ---
  // Make sure nav links work if they exist
  const navLinks = {
    Login: "login.html",
    Process: "homepage.html#process",
    Architecture: "homepage.html#architecture",
    Solutions: "homepage.html#solutions",
    Dashboard: "dashboard.html",
    Create: "create.html",
    Pipeline: "process.html", // Placeholder
    Library: "library.html",
  };

  // Attach click listeners to text links if they match our map
  document.querySelectorAll("a").forEach((link) => {
    const text = link.innerText.trim();
    if (navLinks[text] && link.getAttribute("href") === "#") {
      link.href = navLinks[text];
    }
  });

  // --- Page Specific Logic ---

  // --- Login Persistence Logic ---
  const isLoggedIn = sessionStorage.getItem("isLoggedIn") === "true";

  // If already logged in and on login page, redirect to dashboard
  if (path.endsWith("login.html") && isLoggedIn) {
    window.location.href = "dashboard.html";
    return; // Stop further execution on login page
  }

  // --- Page Specific Logic ---

  // 1. Login Page
  if (page === "login.html") {
    const loginForm = document.querySelector("form");
    if (loginForm) {
      loginForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        if (email === "hola@gmail.com" && password === "hola123") {
          // Success
          sessionStorage.setItem("isLoggedIn", "true");
          window.location.href = "dashboard.html";
        } else {
          alert("Invalid credentials! Try hola@gmail.com / hola123");
        }
      });
    }
  }

  // 2. Create Page
  if (page === "create.html") {
    // File Upload Logic
    const dropZone = document.querySelector(".group\\/drop"); // The drag & drop area
    const fileInput = document.getElementById("file-upload");

    if (dropZone && fileInput) {
      dropZone.addEventListener("click", () => {
        fileInput.click();
      });

      fileInput.addEventListener("change", (e) => {
        if (fileInput.files.length > 0) {
          const count = fileInput.files.length;
          const textP = dropZone.querySelector("p.text-xl");
          if (textP) textP.innerText = `${count} Asset(s) Selected`;
        }
      });
    }

    const generateBtn = document.querySelector("button.bg-primary"); // Assumes the big generate button
    if (generateBtn) {
      generateBtn.addEventListener("click", () => {
        const topic =
          document.querySelector("textarea")?.value || "Untitled Project";
        // Save to local storage for the next steps
        localStorage.setItem("currentProjectTopic", topic);
        localStorage.setItem("currentProjectStatus", "processing");

        // Simulate processing redirect
        window.location.href = "process.html";
      });
    }
  }

  // 3. Process Page
  if (page === "process.html") {
    // Simulate a 4-second delay before "finishing"
    setTimeout(() => {
      window.location.href = "output.html";
    }, 4000);
  }

  // 4. Output Page
  if (page === "output.html") {
    const topic =
      localStorage.getItem("currentProjectTopic") || "Generated Video";
    const projectTitleElement = document.getElementById("project-title");
    if (projectTitleElement) {
      projectTitleElement.innerText = topic;
    }
  }
});
