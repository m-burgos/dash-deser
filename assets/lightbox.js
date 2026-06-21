// Lightbox: click any .expandable-img to show it full-screen in the overlay.
// Click the overlay (or press Escape) to close.
// Uses event delegation so it works on dynamically rendered images.

document.addEventListener("click", function (e) {
    var img = e.target.closest(".expandable-img");
    if (img) {
        var overlay = document.getElementById("lightbox-overlay");
        var lbImg = document.getElementById("lightbox-img");
        if (overlay && lbImg) {
            lbImg.src = img.src;
            overlay.classList.add("active");
        }
        return;
    }

    // Click anywhere on the overlay (including the image) closes it
    var overlay = e.target.closest(".lightbox-overlay");
    if (overlay) {
        overlay.classList.remove("active");
    }
});

document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
        var overlay = document.getElementById("lightbox-overlay");
        if (overlay) overlay.classList.remove("active");
    }
});
