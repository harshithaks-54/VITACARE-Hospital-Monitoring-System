
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".iv-progress-fill").forEach(function (bar) {
        let level = parseInt(bar.dataset.level, 10) || 0;

        level = Math.min(Math.max(level, 0), 100);
        bar.style.width = level + "%";
    });
});
