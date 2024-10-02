const slides = document.querySelectorAll('.slide');
const dots = document.querySelectorAll('.dot');
let currentIndex = 0;

function showSlide(index) {
    const offset = -index * 100;
    document.querySelector('.slides').style.transform = `translateX(${offset}%)`;

    dots.forEach((dot, i) => {
        dot.classList.toggle('active', i === index);
    });
}

dots.forEach((dot, index) => {
    dot.addEventListener('click', () => {
        currentIndex = index;
        showSlide(index);
    });
});

// Automatically cycle through slides
setInterval(() => {
    currentIndex = (currentIndex + 1) % slides.length;
    showSlide(currentIndex);
}, 3000); // Change every 3 seconds


function toggleMenu() {
    const topbar = document.getElementById('topbar');
    const hamburger = document.getElementById('hamburger');

    const open = (topbar.style.bottom === '-60vh')

    const isMenuOpen = topbar.classList.contains('show');

    if (open) {
        // If menu is open, close it and change the icon back to hamburger
        topbar.style.bottom = '100vh';
        topbar.classList.remove('show');
        hamburger.src = 'assets/icons/Hamburger.svg';
    } else {
        // If menu is closed, open it and change the icon to "x"
        topbar.style.bottom = '-60vh';
        topbar.classList.add('show');
        hamburger.src = 'assets/icons/x.svg';
    }
}


hamburger.addEventListener('click', () => {
    toggleMenu();
});