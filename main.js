const cardRow = document.getElementById('cardRow');
const scrollAmount = 300; // Ajusta la cantidad de desplazamiento

function scrollLeft() {
    if (cardRow.scrollLeft === 0) {
        // Si ya estamos en el extremo izquierdo, desplazarse al final
        cardRow.scrollTo({
            left: cardRow.scrollWidth,
            behavior: 'smooth'
        });
    } else {
        // Desplazarse hacia la izquierda
        cardRow.scrollBy({
            left: -scrollAmount,
            behavior: 'smooth'
        });
    }
}

function scrollRight() {
    if (cardRow.scrollLeft + cardRow.clientWidth >= cardRow.scrollWidth) {
        // Si ya estamos en el extremo derecho, volver al inicio
        cardRow.scrollTo({
            left: 0,
            behavior: 'smooth'
        });
    } else {
        // Desplazarse hacia la derecha
        cardRow.scrollBy({
            left: scrollAmount,
            behavior: 'smooth'
        });
    }
}