const fileUpload1 = document.getElementById('fileUpload1');
const uploadText1 = document.getElementById('uploadText1');
const svg1 = document.getElementById('svg1');

fileUpload1.addEventListener('change', (event) => {
    const file = event.target.files[0];
    if (file) {
        uploadText1.textContent = `${file.name}`;
        svg1.style.position = 'absolute';
        svg1.style.opacity = '0';
    } else {
        uploadText1.textContent = 'No file selected';
    }
});

const fileUpload2 = document.getElementById('fileUpload2');
const uploadText2 = document.getElementById('uploadText2');
const svg2 = document.getElementById('svg2');

fileUpload2.addEventListener('change', (event) => {
    const file = event.target.files[0];
    if (file) {
        uploadText2.textContent = `${file.name}`;
        svg2.style.position = 'absolute';
        svg2.style.opacity = '0';
    } else {
        uploadText2.textContent = 'No file selected';
    }
});

const fileUpload3 = document.getElementById('fileUpload3');
const uploadText3 = document.getElementById('uploadText3');
const svg3 = document.getElementById('svg3');

fileUpload3.addEventListener('change', (event) => {
    const file = event.target.files[0];
    if (file) {
        uploadText3.textContent = `${file.name}`;
        svg3.style.position = 'absolute';
        svg3.style.opacity = '0';
    } else {
        uploadText3.textContent = 'No file selected';
    }
});

const pfp = document.getElementById('pfp');
const dropdown = document.getElementById('pfpdropdown');

    pfp.addEventListener('click', function() {
        dropdown.classList.toggle('not-present');
        dropdown.classList.toggle('present');
});

document.addEventListener('click', function(event) {
    if (!dropdown.contains(event.target) && !pfp.contains(event.target)) {
        dropdown.classList.remove('present');
        dropdown.classList.add('not-present');
    }
});