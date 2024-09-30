const actionIcons = document.querySelectorAll(".actionIcon");
const deleteModal = document.getElementById("deleteModal");
const newfolderBtn = document.getElementById("new-folder");
const deletecancelBtn = document.getElementById("deleteCancelBtn");
const uploadCancelBtn = document.getElementById("uploadCancelBtn");
const deleteBtn = document.getElementById("deleteBtn");
const uploadBtn = document.getElementById("uploadBtn");
const fileUpload = document.getElementById("fileUpload");
const uploadModal = document.getElementById("uploadModal");
const successModal = document.getElementById("successModal");
const SaveName = document.getElementById("SaveName");
const masterCheckbox = document.getElementById("masterCheckbox");
const subCheckboxes = document.querySelectorAll(".subCheckbox");

let selectedFolder = null; // Store the selected folder to delete

// Function to open the delete confirmation modal
const openDeleteModal = (folderName) => {
  selectedFolder = folderName;
  deleteModal.style.display = "block";
};

// Function to close the delete confirmation modal
const closeDeleteModal = () => {
  deleteModal.style.display = "none";
};

// Loop through all action icons and add event listeners
actionIcons.forEach((icon, index) => {
  icon.addEventListener("click", () => {
    const actionBox = document.getElementById(`actionBox${index + 1}`);
    console.log("hell" + actionBox);
    actionBox.style.display =
      actionBox.style.display === "block" ? "none" : "block";
    document.addEventListener("click", function outsideClickHandler(event) {
      // Check if the clicked target is not the action box or the icon itself
      if (!actionBox.contains(event.target) && !icon.contains(event.target)) {
        actionBox.style.display = "none";
        document.removeEventListener("click", outsideClickHandler); // Remove the listener once it's triggered
      }
    });
  });
});

// Add event listeners for delete actions
document.querySelectorAll(".delete-action").forEach((deleteAction, index) => {
  deleteAction.addEventListener("click", () => {
    const folderName = `Folder Num ${index + 1}`; // Adjust this to get the actual folder name dynamically
    openDeleteModal(folderName);
  });
});

document.querySelectorAll(".rename-action").forEach((renameAction, index) => {
  renameAction.addEventListener("click", () => {
    const folderName = `Folder Num ${index + 1}`;
    openSuccessModal();
  });
});

// Close modal when clicking cancel button
deletecancelBtn.addEventListener("click", closeDeleteModal);

// Handle delete button click
deleteBtn.addEventListener("click", () => {
  console.log(`Deleting ${selectedFolder}`); // Add your delete logic here
  closeDeleteModal(); // Close modal after deleting
});

// Function to open the success modal
function openSuccessModal() {
  successModal.classList.add("active");
}

// Function to close the success modal
function closeSuccessModal() {
  successModal.classList.remove("active");
}
// Handle submit button in the success modal
SaveName.addEventListener("click", function () {
  const NewName = document.getElementById("NewName").value;
  console.log("New Name: ", NewName);
  closeSuccessModal(); // Close the success modal after submission
});
