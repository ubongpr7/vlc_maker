# CreativeMaker.io

> CreativeMaker.io is a web application that is used to create video with subtitle from just text files and video clips

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [Screenshots](#screenshots)

## Installation


```bash
# Clone the repository
git clone https://github.com/ubongpr7/vlc_maker.git

# Navigate to the project directory
cd vlc_maker
```
```bash
# Set up environment variables
# Create a .env file and add the following keys:

EMAIL_HOST_USER
EMAIL_HOST_PASSWORD
STRIPE_SECRET_KEY
STRIPE_PUBLISHABLE_KEY
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
```
```bash
# Buil the Docker File and Install dependencies
# If you want to build a new docker file for the project, run the following commmand:
docker build -t your_docker_repo .
```
```bash
# Open docker-compose.yml file to and replace nas415/vlc_maker:latest with you your_docker_repo
# If you want to run the application with nas415/vlc_maker:latest
# Pull the Image Here:
docker pull nas415/vlc_maker:latest
```
## Usage

```bash
# To run the application, run the following on your terminal
cd vlc_maker
docker compose up
# Visit the the web at your_ip:8000
```
## Contributing
```bash
# Fork the repository
# Create a new branch for your feature or bugfix
git checkout -b feature-name

# Make changes and commit
git commit -m "Description of the feature added or bug fixed"

# Push to the branch
git push origin feature-name

```
## Screenshots
![image](https://github.com/user-attachments/assets/d8b0f8cf-2e7c-4a48-9245-7613c890afe9)
![image](https://github.com/user-attachments/assets/2c717c15-f627-4236-897f-9f79ee9246d8)
![image](https://github.com/user-attachments/assets/bbebc4c0-5bcb-44df-bc31-d4e9a8bb51ee)
![image](https://github.com/user-attachments/assets/7fad2903-b28c-4cee-a655-33f1b571ce1b)
![image](https://github.com/user-attachments/assets/f70d129a-f08c-4b0c-b2cc-0fa2a2f6fe37)
![image](https://github.com/user-attachments/assets/79ce20ee-1ae8-4a8b-b78d-2fc5163cf03d)

![image](https://github.com/user-attachments/assets/40873c5e-be91-4f18-aea1-7a66936bbdf5)

![image](https://github.com/user-attachments/assets/3272b188-34a4-4362-a995-41ddd6e2adf2)
![image](https://github.com/user-attachments/assets/1bd98c6c-46ab-4c9b-9c2c-7fe8c7fd77ef)

![image](https://github.com/user-attachments/assets/47f0047f-ea9b-4c13-a1e3-a508acac9cbb)
![image](https://github.com/user-attachments/assets/6d6d2e9b-741f-4038-9cd6-1e27bc6b413e)
![image](https://github.com/user-attachments/assets/0e75c28c-e3da-48bc-b896-01e7bfa46735)
