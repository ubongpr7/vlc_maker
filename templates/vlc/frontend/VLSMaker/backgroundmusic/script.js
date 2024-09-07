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


let currentNumber = 2;

document.getElementById('insertButton').addEventListener('click', function() {
    // Increment the number
    currentNumber++;

    // HTML code with the incremented number
    const htmlCode = `
                <div class="uploadmp3" style="display: flex; width: 100%; height: fit-content; justify-content: center; gap: 24px; flex-direction: column;">
                    <div class="text">
                        <span>Upload MP3 <span>${currentNumber}</span>:</span>
                    </div>
                    <div style="width: 100%; box-sizing: border-box; height: fit-content; padding: 16px 24px; border-radius: 8px; border: 1px dashed #19191980; display: flex; align-items: center; position: relative; font-size: 16px; font-weight: 400; line-height: 23.2px; letter-spacing: 0.02em; text-align: center; gap: 14px;">
                        <svg id="svg1" class="svgIcon" width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M17.5 12.5V15.8333C17.5 16.2754 17.3244 16.6993 17.0118 17.0118C16.6993 17.3244 16.2754 17.5 15.8333 17.5H4.16667C3.72464 17.5 3.30072 17.3244 2.98816 17.0118C2.67559 16.6993 2.5 16.2754 2.5 15.8333V12.5M14.1667 6.66667L10 2.5M10 2.5L5.83333 6.66667M10 2.5V12.5" stroke="#191919B2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        <input class="fileInput" type="file" name="uploadScene" id="fileUpload1" style="position: absolute; width: 100%; height: 100%; left: 0; opacity: 0;">                                
                        <div class="output" id="uploadText1" style="font-size: 16px; font-weight: 400; line-height: 23.2px; letter-spacing: 0.02em; text-align: center;">
                            Choose File
                        </div>
                    </div>
                    <div class="text">
                        <span>What Second Should This MP3 Play From? <span style="font-size: 12px;font-weight: 500;line-height: 14.63px;text-align: left;">In Minutes</span></span>
                    </div>
                    <div style="display: flex; gap: 24px; width: 100%;">
                        <div style="display: flex; flex-direction: column; width: 100%; gap: 16px;">
                            <span class="text" style="width: 100%; text-align: left;">Start:</span>
                            <input type="text" placeholder="00:00" class="time" style="padding: 12px 24px; border: 1px solid #E3E3E3; border-radius: 4px;">
                        </div>
                        <div style="display: flex; flex-direction: column; width: 100%; gap: 16px;">
                            <span class="text" style="width: 100%; text-align: left;">End:</span>
                            <input type="text" placeholder="00:00" class="time" style="padding: 12px 24px; border: 1px solid #E3E3E3; border-radius: 4px;">
                        </div>
                    </div>
                </div>
    `;
    
    // Insert the HTML code into the target div
    document.getElementById('targetDiv').insertAdjacentHTML('beforeend', htmlCode);
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