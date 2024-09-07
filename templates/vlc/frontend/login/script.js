// JavaScript to handle the toggle functionality
const toggleIcon = document.querySelector('#toggleIcon');
const password = document.querySelector('#password');
const eyeIcon = document.querySelector('#eye');

toggleIcon.addEventListener('click', function () {
    // Toggle the type attribute
    const type = password.getAttribute('type') === 'password' ? 'text' : 'password';
    password.setAttribute('type', type);

    // Toggle the eye icon (optional)
    eyeIcon.src = type === 'password' ? 'assets/icons/eye-open.svg' : 'assets/icons/eye-off.svg';
});
