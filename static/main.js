function selectAllText(el) {
  const selection = window.getSelection();
  const isRangeSelected = selection && selection.type === "Range";

  if (!isRangeSelected) {
    el.select();
  }
}

function togglePopupDialog(id) {
  document.getElementById(id).classList.toggle("popup-hidden");
}

function closePopupOnOutsideClick(e) {
  if (e.target === e.currentTarget) {
    e.currentTarget.classList.add("popup-hidden");
  }
}

function authenticateJwt() {
  const token = document.getElementById('jwt-token').value;
  fetch('/authenticate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token })
  }).then(res => res.json())
    .then(data => {
      if (data.success) {
        toggleAdminPopup();
        window.location.reload();
      } else {
        alert("Auth failed");
      }
    });
}

function getCurrentSlug() {
    return document.querySelector('meta[name="current-pack-slug"]').content;
}

function onPageShow() {
  // Fixes an issue that the wrong selected item is shown when back-navigating
  {
    const select = document.getElementById("mc-version-range");
    const currentSlug = getCurrentSlug();
    for (const option of select.options) {
      if (option.dataset.slug === currentSlug) {
        select.value = option.value; // Force visual update
        break;
      }
    }
  }

  // Makes all <time> elements show the set timestamp in the user's timezone
  document.querySelectorAll("time[datetime]").forEach((el) => {
    const iso = el.getAttribute("datetime");
    const date = new Date(iso);

    if (!isNaN(date)) {
      // Format using user's locale and timezone
      el.textContent = date.toLocaleString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false
      });
    }
  });
}

window.addEventListener("DOMContentLoaded", () => {
  window.addEventListener("pageshow", onPageShow);
});
