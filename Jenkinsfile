pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = 'customer-recognition-system'
        DOCKER_TAG = "${env.BUILD_NUMBER}"
        DOCKER_FULL_IMAGE = "${DOCKER_IMAGE}:${DOCKER_TAG}"
        DOCKER_HUB_CREDENTIALS = credentials('dockerhub-credentials')
        // Change this to your Docker Hub username
        DOCKER_HUB_USERNAME = 'yourusername'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Lint & Test') {
            steps {
                sh '''
                    # Install linting tools
                    pip install flake8 pytest
                    
                    # Run linting
                    flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
                    
                    # Run unit tests (if available)
                    # pytest -v
                '''
            }
        }
        
        stage('Build Docker Image') {
            steps {
                sh '''
                    docker build -t ${DOCKER_FULL_IMAGE} .
                    docker tag ${DOCKER_FULL_IMAGE} ${DOCKER_HUB_USERNAME}/${DOCKER_FULL_IMAGE}
                '''
            }
        }
        
        stage('Push to Docker Hub') {
            steps {
                sh '''
                    echo ${DOCKER_HUB_CREDENTIALS_PSW} | docker login -u ${DOCKER_HUB_CREDENTIALS_USR} --password-stdin
                    docker push ${DOCKER_HUB_USERNAME}/${DOCKER_FULL_IMAGE}
                '''
            }
        }
        
        stage('Deploy to Development') {
            when {
                branch 'develop'
            }
            steps {
                sh '''
                    # Copy docker-compose file to development server
                    scp docker-compose.yml user@dev-server:/path/to/deployment/
                    
                    # Update .env file on development server
                    ssh user@dev-server "cd /path/to/deployment && echo 'DOCKER_IMAGE=${DOCKER_HUB_USERNAME}/${DOCKER_FULL_IMAGE}' > .env"
                    
                    # Pull and run updated image
                    ssh user@dev-server "cd /path/to/deployment && docker-compose pull && docker-compose up -d"
                '''
            }
        }
        
        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                // Manual approval step before deploying to production
                input message: 'Deploy to production?', ok: 'Yes'
                
                sh '''
                    # Copy docker-compose file to production server
                    scp docker-compose.yml user@prod-server:/path/to/deployment/
                    
                    # Update .env file on production server
                    ssh user@prod-server "cd /path/to/deployment && echo 'DOCKER_IMAGE=${DOCKER_HUB_USERNAME}/${DOCKER_FULL_IMAGE}' > .env"
                    
                    # Pull and run updated image
                    ssh user@prod-server "cd /path/to/deployment && docker-compose pull && docker-compose up -d"
                '''
            }
        }
    }
    
    post {
        always {
            // Clean up Docker images to prevent disk space issues
            sh 'docker system prune -f'
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
            // Add notification steps here (email, Slack, etc.)
        }
    }
} 