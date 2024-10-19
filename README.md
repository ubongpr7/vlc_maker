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



