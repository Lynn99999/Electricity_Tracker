const backToTopButton = document.querySelector("[data-back-to-top]");

if (backToTopButton) {
    function toggleBackToTopButton() {
        if (window.scrollY > 300) {
            backToTopButton.classList.add("is-visible");
        } else {
            backToTopButton.classList.remove("is-visible");
        }
    }

    backToTopButton.addEventListener("click", function () {
        window.scrollTo({
            top: 0,
            behavior: "smooth",
        });
    });

    window.addEventListener("scroll", toggleBackToTopButton);
    toggleBackToTopButton();
}
