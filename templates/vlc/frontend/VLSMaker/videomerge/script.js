document.querySelector('.file-upload-container').addEventListener('change', function(event) {
    if (event.target.classList.contains('fileInput')) {
        const fileInput = event.target;
        const fileName = fileInput.files.length > 0 ? fileInput.files[0].name : 'No file chosen';
        const output = fileInput.nextElementSibling; // Assuming <span> is the next sibling

        if (output && output.classList.contains('output')) {
            output.textContent = fileName;
        }
        
        // Apply styles to the SVG
        const svgIcon = fileInput.previousElementSibling; // Assuming <svg> is the previous sibling
        if (svgIcon && svgIcon.classList.contains('svgIcon')) {
            svgIcon.style.position = 'absolute';
            svgIcon.style.opacity = '0';
        }
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