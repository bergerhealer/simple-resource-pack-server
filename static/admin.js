function selectZipFile() {
  const input = document.getElementById('upload-file-input');
  input.value = '';
  input.click();
}

async function callApi(method, url, body) {
  const res = await fetch(url, {
    method: method,
    headers: (body instanceof FormData) ? undefined : {
      "Content-Type": "application/json"
    },
    body: (body instanceof FormData) ? body : JSON.stringify(body)
  });

  let data = null;
  try {
    data = await res.json();
  } catch (jsonErr) {
    throw new Error("Server returned invalid response.");
  }

  if (!res.ok) {
    const message = data?.error || `Update failed with status ${res.status}`;
    throw new Error(message);
  }

  if (data?.error) {
    throw new Error(data?.error);
  }

  if (data?.redirect_url) {
    window.location.href = data.redirect_url;
  }

  return data;
}

function uploadZipFile() {
  const input = document.getElementById('upload-file-input');
  const file = input.files[0];
  if (!file) {
    return;
  }

  const formData = new FormData();
  formData.append('file', file);

  callApi('POST', `/p/${getCurrentSlug()}/upload`, formData)
    .then(data => {
      if (!data?.redirect_url)
        throw new Error("Upload succeeded, but no redirect URL was provided.");
    }).catch(err => {
      console.error("Upload error:", err);
      alert("Upload failed:" + (err.message || ""));
    });
}

function patchUpdate(updatedJson, successCallback) {
  callApi('PATCH', `/p/${getCurrentSlug()}`, updatedJson)
      .then(successCallback)
      .catch(err => {
        console.error("Update Failed:", err);
        alert("Update Failed: " + (err.message || ""));
        window.location.reload();
      });
}

function replaceWithKeepStyle(element, replacement) {
  const computed = getComputedStyle(element);
  replacement.style.fontSize = computed.fontSize;
  replacement.style.fontFamily = computed.fontFamily;
  replacement.style.lineHeight = computed.lineHeight;
  replacement.style.fontWeight = computed.fontWeight;
  replacement.style.letterSpacing = computed.letterSpacing;

  element.replaceWith(replacement);
}

function makeTitleEditable(h1) {
  const currentText = h1.textContent;
  const input = document.createElement("input");
  input.type = "text";
  input.value = currentText;
  input.style.fontSize = "2em";
  input.style.width = "50%";

  h1.replaceWith(input);
  input.focus();
  input.select();

  input.addEventListener("blur", () => {
    const newText = input.value.trim() || currentText;

    patchUpdate({ name: newText }, () => {
      const revertH1 = document.createElement("h1");
      revertH1.id = "title";
      revertH1.textContent = newText;
      revertH1.ondblclick = () => makeTitleEditable(revertH1);
      input.replaceWith(revertH1);
    })
  });
}

function extractDescriptionText(container) {
  const lines = Array.from(container.querySelectorAll("span")).map(span => {
    return span.innerHTML.trim() === "&nbsp;" ? "" : span.textContent;
  });
  return lines.join("\n");
}

function makeDescriptionEditable(span) {
  const currentText = extractDescriptionText(span);
  const textarea = document.createElement("textarea");
  textarea.value = currentText;

   // textarea.style.fontSize = "1.2em";
  textarea.style.width = "100%";
  textarea.style.boxSizing = "border-box";
  textarea.style.overflow = "hidden";

  // Resize function
  function autoResize(el) {
    el.style.height = "auto";
    el.style.height = el.scrollHeight + "px";
  }

  // Resize after insertion
  setTimeout(() => autoResize(textarea), 0);

  // Resize on input
  textarea.addEventListener("input", () => autoResize(textarea));

  // Trigger resize once on insert
  textarea.style.height = "auto";
  textarea.style.height = textarea.scrollHeight + "px";

  replaceWithKeepStyle(span, textarea);
  textarea.focus();

  textarea.addEventListener("blur", () => {
    const newText = textarea.value.trim() || currentText;

    patchUpdate({ description: newText }, () => {
      const revertSpan = document.createElement("span");
      revertSpan.className = "description-text";
      revertSpan.ondblclick = () => makeDescriptionEditable(revertSpan);

      for (const line of newText.split("\n")) {
        const lineSpan = document.createElement("span");
        lineSpan.textContent = line === "" ? "\u00A0" : line;
        revertSpan.appendChild(lineSpan);
      }

      textarea.replaceWith(revertSpan);
    })
  });
}

function updateVersion() {
  const minecraftVersion = {
    minimum: document.getElementById('edit-min-version').value,
    maximum: document.getElementById('edit-max-version').value
  }

  patchUpdate({ minecraft: minecraftVersion }, () => {
    // Successful, update the selection box too
    const select = document.getElementById('mc-version-range');
    const selectedOption = select.options[select.selectedIndex];
    const tags = selectedOption.dataset.tags
    selectedOption.textContent = `${minecraftVersion.minimum} – ${minecraftVersion.maximum}${tags ? ' ' + tags : ''}`;
  });
}

function duplicatePack() {
  callApi('POST', `/p/${getCurrentSlug()}/duplicate`, {})
    .then(data => {
      if (!data?.redirect_url)
        throw new Error("Duplication succeeded, but no redirect URL was provided.");
    }).catch(err => {
      console.error("Duplicate error:", err);
      alert("Duplicate failed:" + (err.message || ""));
    });
}

function deletePack() {
  patchUpdate({ main: false }, () => {
    alert("Pack will no longer be shown in the main selection list");
    window.location.reload();
  })
}
