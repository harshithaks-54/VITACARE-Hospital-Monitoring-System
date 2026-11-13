document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".occupancy-fill").forEach(function (bar) {
        let percentage = parseInt(bar.dataset.occupancy, 10) || 0;

        percentage = Math.min(Math.max(percentage, 0), 100);
        bar.style.width = percentage + "%";
    });
});