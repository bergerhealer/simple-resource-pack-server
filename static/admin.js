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
