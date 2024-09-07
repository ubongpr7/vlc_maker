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