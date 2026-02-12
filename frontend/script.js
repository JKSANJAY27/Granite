// ── Granite Frontend Script ─────────────────────────────────────────
// Integrates the frontend with the FastAPI backend at /api/*

// If opened from file:// (not served by FastAPI), target localhost
const API_BASE =
  window.location.protocol === "file:"
    ? "http://localhost:8000"
    : "";

document.addEventListener("DOMContentLoaded", () => {
  const path = window.location.pathname;
  const page = path.split("/").pop() || "index.html";

  // ── Login Persistence ───────────────────────────────────────────
  const isLoggedIn = sessionStorage.getItem("isLoggedIn") === "true";
  if (path.endsWith("login.html") && isLoggedIn) {
    window.location.href = "dashboard.html";
    return;
  }

  // ── Page: Login ─────────────────────────────────────────────────
  if (page === "login.html") {
    const loginForm = document.querySelector("form");
    if (loginForm) {
      loginForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;
        if (email === "hola@gmail.com" && password === "hola123") {
          sessionStorage.setItem("isLoggedIn", "true");
          window.location.href = "dashboard.html";
        } else {
          alert("Invalid credentials! Try hola@gmail.com / hola123");
        }
      });
    }
  }

  // ── Page: Create ────────────────────────────────────────────────
  if (page === "create.html") {
    const dropZone = document.querySelector(".group\\/drop");
    const fileInput = document.getElementById("file-upload");
    const generateBtn = document.querySelector("button.bg-primary");

    // Click-to-upload
    if (dropZone && fileInput) {
      dropZone.addEventListener("click", () => fileInput.click());

      fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
          const file = fileInput.files[0];
          const textP = dropZone.querySelector("p.text-xl");
          if (textP) textP.innerText = `📄 ${file.name}`;
          // Also update the subtitle
          const subP = dropZone.querySelector("p.text-white\\/40");
          if (subP) {
            const sizeMB = (file.size / 1024 / 1024).toFixed(1);
            subP.innerText = `${sizeMB} MB — Ready to upload`;
          }
        }
      });
    }

    // Generate button → POST /api/generate
    if (generateBtn) {
      generateBtn.addEventListener("click", async () => {
        const description =
          document.getElementById("topic-description")?.value?.trim() || "";
        const file = fileInput?.files?.[0] || null;

        if (!file && !description) {
          alert("Please upload a PDF document or enter a topic description.");
          return;
        }

        // Show loading state
        generateBtn.disabled = true;
        generateBtn.innerHTML = `
          <div class="loader" style="width:24px;height:24px;border-width:3px;"></div>
          <span>Starting Pipeline...</span>
        `;

        try {
          const formData = new FormData();
          if (file) formData.append("file", file);
          if (description) formData.append("description", description);

          const res = await fetch(`${API_BASE}/api/generate`, {
            method: "POST",
            body: formData,
          });

          if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Failed to start pipeline");
          }

          const data = await res.json();
          const jobId = data.job_id;

          // Save state for subsequent pages
          localStorage.setItem("graniteJobId", jobId);
          localStorage.setItem(
            "currentProjectTopic",
            description || file?.name || "Generated Video"
          );
          if (file) localStorage.setItem("graniteFileName", file.name);

          // Redirect to process page
          window.location.href = "process.html";
        } catch (err) {
          alert(`Error: ${err.message}`);
          generateBtn.disabled = false;
          generateBtn.innerHTML = `
            Generate Video
            <span class="material-icons text-4xl">bolt</span>
          `;
        }
      });
    }
  }

  // ── Page: Process (Pipeline Status) ─────────────────────────────
  if (page === "process.html") {
    const jobId = localStorage.getItem("graniteJobId");
    if (!jobId) {
      window.location.href = "create.html";
      return;
    }

    // Show the source file name
    const sourceHash = document.getElementById("source-hash");
    const fileName = localStorage.getItem("graniteFileName") || "—";
    if (sourceHash) sourceHash.textContent = fileName;

    // Pipeline step IDs in order
    const stepIds = [
      "step-extraction",
      "step-planning",
      "step-animation",
      "step-narration",
      "step-composition",
      "step-quality",
    ];
    const stepNames = [
      "extraction",
      "planning",
      "animation",
      "narration",
      "composition",
      "quality",
    ];
    const stepLabels = [
      "Extracting content from document",
      "Planning lesson structure",
      "Generating Manim animation",
      "Creating narration audio",
      "Composing final video",
      "Quality checking output",
    ];

    let lastStep = "";
    let pollCount = 0;

    function addTerminalLine(tag, message, isSuccess = false) {
      const log = document.getElementById("terminal-log");
      if (!log) return;
      const container = log.querySelector(".space-y-1\\.5");
      if (!container) return;

      const now = new Date();
      const ts = `[${now.toTimeString().slice(0, 8)}.${String(now.getMilliseconds()).padStart(3, "0")}]`;

      const line = document.createElement("div");
      line.className = "flex gap-6";
      line.innerHTML = `
        <span class="text-zinc-700">${ts}</span>
        <span class="${isSuccess ? "text-white font-bold uppercase" : "text-primary-neon font-bold uppercase"}">[${tag}]</span>
        <span class="text-zinc-400">${message}</span>
      `;
      container.appendChild(line);

      // Auto-scroll to bottom
      log.scrollTop = log.scrollHeight;
    }

    function updatePipelineStep(currentStep) {
      const currentIdx = stepNames.indexOf(currentStep);
      if (currentIdx < 0) return;

      stepIds.forEach((id, idx) => {
        const el = document.getElementById(id);
        if (!el) return;

        const badge = el.querySelector(
          ".col-span-4 span, .col-span-4 .step-badge"
        );
        const icon = el.querySelector(
          ".col-span-2 > div, .col-span-2.lg\\:col-span-3 > div, .step-icon"
        );
        const iconContainer = el.querySelector(".col-span-2, [class*='col-span-2 lg:col-span-3']");
        const title = el.querySelector("h4");
        const desc = el.querySelector("p, .step-desc");

        if (idx < currentIdx) {
          // Completed
          el.classList.remove("opacity-50", "grayscale");
          el.style.opacity = "1";
          el.style.filter = "none";
          if (badge) {
            badge.className =
              "px-3 py-1 bg-primary-neon/10 text-primary-neon text-[9px] font-bold uppercase tracking-widest rounded-pill border border-primary-neon/20";
            badge.textContent = "Success";
          }
          if (title) title.className = "text-sm font-bold tracking-wider text-white uppercase";
          if (desc) {
            desc.className = "text-[10px] text-zinc-500 font-mono";
            desc.textContent = stepLabels[idx] + " — done ✓";
          }
        } else if (idx === currentIdx) {
          // Active
          el.classList.remove("opacity-50", "grayscale");
          el.style.opacity = "1";
          el.style.filter = "none";
          if (badge) {
            badge.className =
              "inline-flex items-center gap-2 px-3 py-1 bg-white text-black text-[9px] font-black uppercase tracking-widest rounded-pill";
            badge.innerHTML = `<span class="w-1.5 h-1.5 bg-black rounded-full animate-ping"></span> Processing`;
          }
          if (title) title.className = "text-lg font-bold tracking-tight text-white uppercase italic";
          if (desc) {
            desc.className = "text-xs text-primary-neon font-mono animate-pulse";
            desc.textContent = stepLabels[idx] + "...";
          }
        }
        // else: future steps stay dimmed (default)
      });
    }

    async function pollStatus() {
      try {
        const res = await fetch(`${API_BASE}/api/status/${jobId}`);
        if (!res.ok) {
          if (res.status === 404) {
            // Server may have restarted — don't redirect, just warn and retry
            addTerminalLine("Warn", "Job not found on server (possible restart). Retrying...");
            setTimeout(pollStatus, 5000);
            return;
          }
          throw new Error(`Status check failed: ${res.status}`);
        }

        const data = await res.json();
        pollCount++;

        // Update progress bars
        const topBar = document.getElementById("top-progress-bar");
        const frameBar = document.getElementById("frame-progress-bar");
        const progressLabel = document.getElementById("progress-label");
        if (topBar) topBar.style.width = `${data.progress}%`;
        if (frameBar) frameBar.style.width = `${data.progress}%`;
        if (progressLabel) progressLabel.textContent = `${data.progress}%`;

        // Update stage badge and status label
        const stageBadge = document.getElementById("stage-badge");
        const statusLabel = document.getElementById("status-label");
        if (stageBadge) {
          const stepIdx = stepNames.indexOf(data.current_step);
          stageBadge.textContent =
            stepIdx >= 0 ? `Stage ${String(stepIdx + 1).padStart(2, "0")}` : data.current_step;
        }
        if (statusLabel) statusLabel.textContent = data.message || "Processing...";

        // Update pipeline steps visualization
        if (data.current_step !== lastStep && data.current_step !== "queued") {
          updatePipelineStep(data.current_step);

          const stepIdx = stepNames.indexOf(data.current_step);
          if (stepIdx >= 0) {
            addTerminalLine("Pipeline", stepLabels[stepIdx] + "...");
          }
          // Log completion of previous step
          if (lastStep && lastStep !== "queued") {
            const prevIdx = stepNames.indexOf(lastStep);
            if (prevIdx >= 0) {
              addTerminalLine("Success", stepLabels[prevIdx] + " — completed", true);
            }
          }
          lastStep = data.current_step;
        }

        // Check terminal states
        if (data.status === "completed") {
          addTerminalLine("Success", "Pipeline completed successfully! ✅", true);

          // Mark all steps as complete
          stepIds.forEach((id) => {
            const el = document.getElementById(id);
            if (!el) return;
            el.classList.remove("opacity-50", "grayscale");
            el.style.opacity = "1";
            el.style.filter = "none";
            const badge = el.querySelector(".col-span-4 span, .col-span-4 .step-badge");
            if (badge) {
              badge.className =
                "px-3 py-1 bg-primary-neon/10 text-primary-neon text-[9px] font-bold uppercase tracking-widest rounded-pill border border-primary-neon/20";
              badge.textContent = "Success";
            }
          });

          // Redirect to output page after a brief delay
          setTimeout(() => {
            window.location.href = "output.html";
          }, 2000);
          return; // Stop polling
        }

        if (data.status === "failed") {
          addTerminalLine("Error", `Pipeline failed: ${data.error || data.message}`);
          if (statusLabel) statusLabel.textContent = "PIPELINE FAILED";
          if (stageBadge) {
            stageBadge.textContent = "Failed";
            stageBadge.className =
              "px-3 py-1 bg-red-500/10 text-red-400 text-[10px] font-bold uppercase tracking-widest rounded-pill border border-red-500/20";
          }
          return; // Stop polling
        }

        // Continue polling
        setTimeout(pollStatus, 3000);
      } catch (err) {
        console.error("Poll error:", err);
        addTerminalLine("Warn", `Connection issue: ${err.message}. Retrying...`);
        setTimeout(pollStatus, 5000);
      }
    }

    // Start polling
    addTerminalLine("System", "Connected to Granite pipeline server");
    addTerminalLine("System", `Job ID: ${jobId}`);
    setTimeout(pollStatus, 1000);
  }

  // ── Page: Output ────────────────────────────────────────────────
  if (page === "output.html") {
    const jobId = localStorage.getItem("graniteJobId");
    const topic =
      localStorage.getItem("currentProjectTopic") || "Generated Video";

    // Set project title
    const projectTitle = document.getElementById("project-title");
    if (projectTitle) projectTitle.textContent = topic;

    // Set prompt/description display
    const promptDisplay = document.getElementById("prompt-display");
    if (promptDisplay) {
      promptDisplay.textContent = topic ? `"${topic}"` : "No description provided";
    }

    // Load video
    const video = document.getElementById("output-video");
    const loadingOverlay = document.getElementById("video-loading");

    if (video && jobId) {
      const videoUrl = `${API_BASE}/api/video/${jobId}`;
      video.src = videoUrl;

      video.addEventListener("loadeddata", () => {
        if (loadingOverlay) loadingOverlay.style.display = "none";
      });

      video.addEventListener("error", () => {
        if (loadingOverlay) {
          loadingOverlay.innerHTML = `
            <div class="flex flex-col items-center gap-4">
              <span class="material-icons text-4xl text-red-400">error_outline</span>
              <span class="text-sm font-mono text-white/40">Failed to load video</span>
              <span class="text-xs text-white/20">The video may still be processing</span>
            </div>
          `;
        }
      });
    } else if (loadingOverlay) {
      loadingOverlay.innerHTML = `
        <div class="flex flex-col items-center gap-4">
          <span class="material-icons text-4xl text-white/20">videocam_off</span>
          <span class="text-sm font-mono text-white/40">No video available</span>
        </div>
      `;
    }

    // Download button
    const downloadBtn = document.getElementById("download-btn");
    if (downloadBtn && jobId) {
      downloadBtn.addEventListener("click", () => {
        const a = document.createElement("a");
        a.href = `${API_BASE}/api/video/${jobId}`;
        a.download = "granite_output.mp4";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      });
    }
  }
});
