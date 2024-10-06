const slides = document.querySelectorAll(".slide");
const dots = document.querySelectorAll(".dot");
let currentIndex = 0;

function showSlide(index) {
  const offset = -index * 100;
  document.querySelector(".slides").style.transform = `translateX(${offset}%)`;

  dots.forEach((dot, i) => {
    dot.classList.toggle("active", i === index);
  });
}

dots.forEach((dot, index) => {
  dot.addEventListener("click", () => {
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
  const topbar = document.getElementById("topbar");
  const hamburger = document.getElementById("hamburger");

  // Check if the topbar is currently hidden (offscreen)
  const open = topbar.style.top === "0px";

  if (open) {
    // If menu is open, close it and change the icon back to hamburger
    topbar.style.top = "-497px"; // Move topbar offscreen
    hamburger.src = "{% statc 'assets/icons/Hamburger.svg' %}";
  } else {
    // If menu is closed, open it and change the icon to "x"
    topbar.style.top = "0"; // Slide topbar into view
    hamburger.src = "{% static 'assets/icons/x.svg' %}";
  }
}

hamburger.addEventListener("click", () => {
  toggleMenu();
});
