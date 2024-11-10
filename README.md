# **CI/CD Pipeline for Flask App Deployment on AWS using Docker, Terraform, Ansible, and GitHub Actions**
This project demonstrates deploying a Flask application using a CI/CD pipeline set up with Terraform, Ansible, and GitHub Actions. The infrastructure is provisioned using Terraform, Docker is managed with Ansible, and the application is built and deployed using a GitHub Actions pipeline.

## Project Overview
1. **Provisioning Infrastructure**: Two AWS EC2 instances are created:
   - **Control Node**: Amazon Linux with Ansible installed.
   - **Host Node**: Ubuntu with Docker installed.
2. **Configuration Management**: Ansible is used to configure the host node, installing and enabling Docker to run on boot.
3. **Application Deployment**: A Flask app is containerized using a Dockerfile and deployed on the host node via GitHub Actions.

## **Steps to recreate this project**
1. **Prerequisites**
   - AWS CLI and credentials set up locally.
   - Terraform installed on your local system.
   - A GitHub repository for your Flask application and Dockerfile.
   - Docker Hub account with credentials for GitHub Actions.
   - Basic knowledge of Ansible and YAML files.
2. **Provision Infrastructure Using Terraform**
   **Terraform Configuration**
   1. Write a Terraform script to:
      - Create two EC2 instances:
        - Amazon Linux (control node).
        - Ubuntu (host node).
      - Configure security groups to allow inbound traffic on ports:
        - **22** for SSH.
        - **80** for HTTP.
        - **5000** for flask application.
        - Allow all outbound traffic.
    2. `main.tf`

       ```hcl
       resource "aws_instance" "amazon_linux" {
        ami = "ami-00385a401487aefa4"
        instance_type = "t2.micro"
        subnet_id = aws_subnet.subnet.id
        vpc_security_group_ids = [aws_security_group.sg.id]
        key_name = aws_key_pair.my_key_pair.key_name
        associate_public_ip_address = true
      
        user_data = <<-EOF
                      #!/bin/bash
                      sudo yum update -y
                      sudo yum install -y ansible
                      EOF
      
        tags = {
          Name = "amazon_linux"
        }
        }
        
        
        resource "aws_instance" "ubuntu" {
          ami = "ami-0a422d70f727fe93e"
          instance_type = "t2.micro"
          subnet_id = aws_subnet.subnet.id
          vpc_security_group_ids = [aws_security_group.sg.id]
          key_name = aws_key_pair.my_key_pair.key_name
          associate_public_ip_address = true
        
          user_data = <<-EOF
                        sudo apt update -y
                        sudo apt install -y python3 python3-pip
                        EOF
        
          tags = {
            Name = "ubuntu"
          }
        }
       ```
   3. Initialize and apply Terraform:

      ```bash
      terraform init
      terraform apply
      ```
3. **Configure the Control Node**
   - Log into the control node via SSH:
     
     ```bash
     ssh -i <your-key.pem> ec2-user@<ControlNodePublicIP>
     ```
   - Set Up SSH Access to the Host Node:
     - Copy the private key to the control node.
     - Test the connectivity:
  
     ```bash
     ssh -i "your-key.pem" ubuntu@<HostNodePrivateIP>
     ```
4. **Configure the Host Node with Ansible**
   1. Add Host node's IP in `/etc/ansible/hosts`
   2. **Write an Ansible Playbook**: `install_docker.yml`:

      ```yaml
      ---
      - name: Install Docker and configure it to start on boot
        hosts: all
        become: yes  # Ensure tasks run with root privileges
      
        tasks:
          # Step 1: Install required dependencies
          - name: Install required dependencies for Docker
            apt:
              name:
                - apt-transport-https
                - ca-certificates
                - curl
                - software-properties-common
              state: present
              update_cache: yes
      
          # Step 2: Add Docker GPG key
          - name: Add Docker GPG key
            apt_key:
              url: https://download.docker.com/linux/ubuntu/gpg
              state: present
      
          # Step 3: Add Docker APT repository
          - name: Add Docker APT repository
            apt_repository:
              repo: deb [arch=amd64] https://download.docker.com/linux/ubuntu jammy stable
              state: present
      
          # Step 4: Install Docker
          - name: Install Docker
            apt:
              name: docker-ce
              state: latest
              update_cache: yes
      
          # Step 5: Enable Docker to start at boot
          - name: Enable Docker to start at boot
            systemd:
              name: docker
              enabled: yes
              state: started
      ```
   3. **Run the Playbook**

      ```bash
      ansible-playbook install_docker.yml
      ```
5. **Prepare Your GitHub Repository**
   1. Add the flask app and docker file
      - Flask `app.py`
        
        ```python
        from flask import Flask

        app = Flask(__name__)
        
        @app.route('/')
        def home():
            return '''  <html>
                        <head>
                        <title>CI/CD</title>
                        </head>
                        <body>
                        <h1> Hello World, I am a flask app running in a docker container. </h1>
                        </body>
                        </html>'''
        
        if __name__ == '__main__':
            app.run(debug=True, host='0.0.0.0', port=5000)
      ```
    - `Dockerfile`
   
      ```docker
      # Use an official Python runtime as the base image
      FROM python:3.9-slim
      
      # Set the working directory in the container
      WORKDIR /app
      
      # Copy the current directory contents into the container
      COPY . .
      
      # Install the required Python packages
      RUN pip install --no-cache-dir -r requirements.txt
      
      # Expose Flask's default port
      EXPOSE 5000
      
      # Set the Flask app environment variable
      ENV FLASK_APP=app.py
      
      # Run the Flask app
      CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
      ```
   2. Commit the repository and push it to GitHub.
6. **Set Up Docker Hub**
   1. Create a New Repository on Docker Hub named `flask-app`
   2. Generate and note down your **Docker Hub username** and **password** for GitHub Actions.

7. **Setup Github Actions for CI/CD**
   1. Create a `.github/workflows/pipeline.yml` file in your GitHub repository:
      ```yaml
      name: CI/CD Pipeline for Docker App

      on:
        push:
          branches:
            - main  
      
      jobs:
        build:
          runs-on: ubuntu-latest
      
          steps:
          - name: Checkout code
            uses: actions/checkout@v3
      
          - name: Set up Docker Buildx
            uses: docker/setup-buildx-action@v2
      
          - name: Login to Docker Hub
            uses: docker/login-action@v2
            with:
              username: ${{ secrets.DOCKER_USERNAME }}
              password: ${{ secrets.DOCKER_PASSWORD }}
      
          - name: Build and push Docker image
            run: |
              docker build -t ${{ secrets.DOCKER_USERNAME }}/app:latest .
              docker push ${{ secrets.DOCKER_USERNAME }}/app:latest
      
        deploy:
          needs: build
          runs-on: ubuntu-latest
      
          steps:
          - name: Checkout code
            uses: actions/checkout@v3
      
          - name: Set up SSH
            uses: webfactory/ssh-agent@v0.7.0
            with:
              ssh-private-key: ${{ secrets.EC2_SSH_PRIVATE_KEY }}
      
          - name: Deploy Docker container to EC2
            run: |
              ssh -o StrictHostKeyChecking=no ubuntu@54.170.110.187 \
              'sudo docker pull ${{ secrets.DOCKER_USERNAME }}/app:latest && \
               sudo docker stop app || true && \
               sudo docker rm app || true && \
               sudo docker run -d --name app -p 5000:5000 ${{ secrets.DOCKER_USERNAME }}/app:latest'
      ```
   2. Configure Repository Secrets:
      - Add the following secrets in your GitHub repository:
        - `DOCKER_USERNAME`: Your Docker Hub username.
        - `DOCKER_PASSWORD`: Your Docker Hub password.
        - `EC2_SSH_PRIVATE_KEY`: The private key for SSH access to the EC2 instance.
       
  8. **Verify the Deployment**
     1. Access the Flask application by navigating to `http://<HostNodePublicIP>:5000` in your browser.
     2. You should see `Hello, World!`.

  9. **Clean Up Resources**
      - To avoid incurring unnecessary costs, delete the resources:
        ```bash
        terraform destroy
        ```

# **Conclusion**
This project automates the end-to-end process of deploying a Flask app on AWS EC2 instances using modern DevOps tools. Docker Hub serves as the central image repository, while GitHub Actions streamlines the CI/CD workflow.
