document.addEventListener("DOMContentLoaded", () => {
    const cardRow = document.getElementById('cardRow');
    const scrollAmount = 300;

    function scrollLeft() {
        if (cardRow.scrollLeft === 0) {
            cardRow.scrollTo({
                left: cardRow.scrollWidth,
                behavior: 'smooth'
            });
        } else {
            cardRow.scrollBy({
                left: -scrollAmount,
                behavior: 'smooth'
            });
        }
    }

    function scrollRight() {
        if (cardRow.scrollLeft + cardRow.clientWidth >= cardRow.scrollWidth) {
            cardRow.scrollTo({
                left: 0,
                behavior: 'smooth'
            });
        } else {
            cardRow.scrollBy({
                left: scrollAmount,
                behavior: 'smooth'
            });
        }
    }

    // Vincula las funciones a los botones
    document.querySelector(".scroll-button.left").onclick = scrollLeft;
    document.querySelector(".scroll-button.right").onclick = scrollRight;
});
