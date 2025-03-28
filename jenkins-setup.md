# Setting Up Jenkins for Customer Recognition System

This guide will help you set up a CI/CD pipeline for your Customer Recognition System using Jenkins.

## Prerequisites

- Jenkins server (standalone or Docker-based)
- Jenkins plugins:
  - Docker Pipeline
  - Pipeline
  - Git plugin
  - Credentials Binding
  - Blue Ocean (optional but recommended)
- Docker installed on Jenkins server
- Access to Docker Hub or a private Docker registry

## Jenkins Server Setup

### Option 1: Run Jenkins using Docker

```bash
docker run -d --name jenkins -p 8080:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/jenkins:lts
```

### Option 2: Install Jenkins on a server

Follow the [official Jenkins installation guide](https://www.jenkins.io/doc/book/installing/) for your platform.

## Initial Jenkins Configuration

1. Access Jenkins at http://your-jenkins-server:8080
2. Follow the setup wizard to install suggested plugins
3. Create an admin account

## Install Required Plugins

1. Go to "Manage Jenkins" > "Manage Plugins"
2. In the "Available" tab, search and install:
   - Docker Pipeline
   - Pipeline
   - Git plugin
   - Credentials Binding
   - Blue Ocean (optional)
3. Restart Jenkins after installation

## Configure Docker Hub Credentials

1. Go to "Manage Jenkins" > "Manage Credentials"
2. Click on "Jenkins" store
3. Click on "Global credentials (unrestricted)"
4. Click "Add Credentials" 
5. Select "Username with password"
6. Enter your Docker Hub username and password
7. Set ID as "dockerhub-credentials"
8. Click "OK"

## Create a Jenkins Pipeline

1. From the Jenkins dashboard, click "New Item"
2. Enter a name for your pipeline (e.g., "customer-recognition-cicd")
3. Select "Pipeline" and click "OK"
4. In the configuration page:
   - Under "Pipeline", select "Pipeline script from SCM"
   - Set SCM to "Git"
   - Enter your repository URL
   - Specify the branch to build (e.g., */main)
   - Set "Script Path" to "Jenkinsfile"
5. Click "Save"

## Update the Jenkinsfile

Modify the provided Jenkinsfile in your project:

1. Update the `DOCKER_HUB_USERNAME` variable with your Docker Hub username
2. Update server details in deployment stages:
   - Replace `user@dev-server` and `user@prod-server` with actual server details
   - Update deployment paths `/path/to/deployment/` with your target directories

## Setup SSH Keys for Deployment

To enable Jenkins to deploy to your servers:

1. Generate SSH keys on Jenkins server:
   ```bash
   ssh-keygen -t rsa -b 4096
   ```

2. Add the public key to the `authorized_keys` file on your deployment servers:
   ```bash
   cat ~/.ssh/id_rsa.pub | ssh user@dev-server "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
   cat ~/.ssh/id_rsa.pub | ssh user@prod-server "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
   ```

3. Add the private key to Jenkins credentials:
   - Go to "Manage Jenkins" > "Manage Credentials"
   - Add a new "SSH Username with private key" credential
   - Set ID as "deployment-ssh-key"
   - Enter the private key content

## First Pipeline Run

1. Go to your pipeline page
2. Click "Build Now" to start the first build
3. Check the console output to make sure everything works

## Integrating with GitHub Webhooks (Optional)

To automatically trigger builds when code is pushed:

1. In your pipeline configuration, check "GitHub hook trigger for GITScm polling"
2. In your GitHub repository, go to "Settings" > "Webhooks"
3. Add a new webhook:
   - Set Payload URL to http://your-jenkins-server:8080/github-webhook/
   - Set Content type to application/json
   - Select "Just the push event"
   - Click "Add webhook"

## Creating Branch-Specific Pipelines (Optional)

1. Use the "Multibranch Pipeline" job type instead of "Pipeline"
2. Configure it to scan for branches in your repository
3. Jenkins will automatically create pipelines for detected branches
4. The Jenkinsfile's conditional stages will determine what actions are taken for each branch

## Troubleshooting

- **Docker permission issues**: Ensure the Jenkins user has access to Docker
  ```bash
  sudo usermod -aG docker jenkins
  sudo systemctl restart jenkins
  ```

- **SSH connection issues**: Test the SSH connection manually:
  ```bash
  ssh -i /path/to/private_key user@server
  ```

- **Pipeline syntax errors**: Use Jenkins' built-in "Pipeline Syntax" generator to help create valid syntax 