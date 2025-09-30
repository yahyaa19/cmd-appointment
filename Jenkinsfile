pipeline {
  agent any

  environment {
    DOCKER_IMAGE = 'appointment-service'
    DOCKER_TAG = "${env.BUILD_NUMBER}"
    VENV_PATH = "${WORKSPACE}/venv"
    PYTHON = "${VENV_PATH}/Scripts/python"
    PIP = "${VENV_PATH}/Scripts/pip"
    ENV_FILE = '.env.test'
  }

  options {
    buildDiscarder(logRotator(numToKeepStr: '10'))
    timeout(time: 30, unit: 'MINUTES')
    timestamps()
  }

  stages {
    stage('Checkout') {
      steps {
        checkout([
          $class: 'GitSCM',
          branches: [[name: '*/main']],
          userRemoteConfigs: [[url: 'https://github.com/yahyaa19/cmd-appointment.git']],
          extensions: [[$class: 'CleanBeforeCheckout']]
        ])
      }
    }

    stage('Setup Python Environment') {
      steps {
        script {
          echo 'Setting up Python environment...'
          
          // Check if virtual environment already exists
          if (fileExists("${VENV_PATH}")) {
            echo 'Virtual environment already exists. Skipping creation.'
          } else {
            echo 'Creating new virtual environment...'
            
            // Try to find a working Python
            def pythonExe = 'python'
            def pythonFound = false
            
            // Check if system Python works
            def pythonCheck = bat(returnStatus: true, script: 'python --version')
            if (pythonCheck == 0) {
              // Verify Python can import modules
              def verifyPython = bat(returnStatus: true, script: 'python -c "import sys; print(sys.executable)"')
              if (verifyPython == 0) {
                pythonFound = true
              }
            }
            
            if (!pythonFound) {
              // Try known Python locations
              def pythonPaths = [
                'C:\\Python39\\python.exe',
                'C:\\Python310\\python.exe',
                'C:\\Python311\\python.exe',
                'C:\\Program Files\\Python39\\python.exe',
                'C:\\Program Files\\Python310\\python.exe',
                'C:\\Program Files\\Python311\\python.exe'
              ]
              
              for (path in pythonPaths) {
                echo "Trying Python at: ${path}"
                def check = bat(returnStatus: true, script: "\"${path}\" -c \"import sys; print(sys.executable)\"")
                if (check == 0) {
                  pythonExe = "\"${path}\""
                  pythonFound = true
                  echo "Found working Python at: ${path}"
                  break
                }
              }
              
              if (!pythonFound) {
                error('No working Python installation found. Please install Python 3.8+ and ensure it\'s in the system PATH.')
              }
            }
            
            // Create virtual environment
            try {
              bat """
                ${pythonExe} -m venv ${VENV_PATH}
                ${PIP} install --upgrade pip setuptools wheel
                ${PIP} install -r requirements.txt
              """
            } catch (Exception e) {
              error("Failed to set up Python environment: ${e.message}")
            }
          }
          
          // Verify the virtual environment works
          def venvCheck = bat(returnStatus: true, script: "${PYTHON} -c \"import sys; print('Python version:', sys.version)\"")
          if (venvCheck != 0) {
            error('Virtual environment setup failed. Please check the logs.')
          }
          
          echo 'Python environment setup completed successfully.'
        }
      }
    }

    // stage('Code Quality & Linting') {
    //   parallel {
    //     stage('Run Flake8') {
    //       steps {
    //         script {
    //           bat "${PYTHON} -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics"
    //           bat "${PYTHON} -m flake8 . --count --max-complexity=10 --max-line-length=127 --statistics"
    //         }
    //       }
    //     }
    //     stage('Run Black') {
    //       steps {
    //         script {
    //           bat "${PYTHON} -m black --check --diff --color ."
    //         }
    //       }
    //     }
    //     stage('Run Isort') {
    //       steps {
    //         script {
    //           bat "${PYTHON} -m isort --check-only --diff ."
    //         }
    //       }
    //     }
    //   }
    // }

    // stage('Security Scanning') {
    //   parallel {
    //     stage('Bandit Security Scan') {
    //       steps {
    //         script {
    //           bat "${PYTHON} -m bandit -r . -c pyproject.toml"
    //         }
    //       }
    //     }
    //     stage('Dependency Check') {
    //       steps {
    //         script {
    //           bat "${PIP} install safety"
    //           bat "safety check --full-report"
    //         }
    //       }
    //     }
    //   }
    // }

    stage('Testing') {
       environment {
         // These variables are picked up by docker-compose.test.yml to configure the MySQL test database.
         // Replace 'rootsecret', 'appuser', 'appsecret' with values from your .env or Jenkins credentials if you changed them.
         MYSQL_ROOT_PASSWORD = 'rootsecret'
         MYSQL_DATABASE = 'appointment_test_db' // Ensure this matches the DB name in docker-compose.test.yml
         MYSQL_USER = 'appuser'
         MYSQL_PASSWORD = 'appsecret'
        // The DATABASE_URL for tests connecting from inside the 'test' service to the 'mysql' service
        TEST_DATABASE_URL = 'mysql+pymysql://appuser:appsecret@mysql:3306/appointment_test_db?charset=utf8mb4'
      }
       steps {
         script {
          echo 'Starting Dockerized test environment...'
          bat 'docker-compose -f docker-compose.test.yml up -d --build --wait'

          echo 'Running all unit and integration tests...'
          // The DATABASE_URL for pytest itself is now taken from the stage environment
           bat """
            ${PYTHON} -m pytest tests/ \
               --cov=app \
               --cov-report=xml:coverage.xml \
               --cov-report=term \
               -v \
              --junitxml=test-results/all-tests.xml
              --ignore=tests/performance \
              --ignore=tests/security
           """
         }
       }
       post {
         always {
          bat 'docker-compose -f docker-compose.test.yml down --volumes --remove-orphans'
           junit 'test-results/all-tests.xml'
           publishHTML(target: [
             allowMissing: false,
             alwaysLinkToLastBuild: false,
             keepAll: true,
             reportDir: 'htmlcov',
             reportFiles: 'index.html',
             reportName: 'Combined Coverage Report'
           ])
         }
       }
     }

    stage('Build Docker Image') {
      when {
        branch 'main'
      }
      steps {
        script {
          def imageName = "${DOCKER_IMAGE}:${DOCKER_TAG}"
          bat "docker build -t ${imageName} ."

          if (env.BRANCH_NAME == 'main') {
            bat "docker tag ${imageName} ${DOCKER_IMAGE}:latest"
            echo "Image tagged as latest"
          }
          bat 'docker images'
        }
      }
    }

  }

  post {
    always {
      node('built-in') {
        script {
          try {
            cleanWs()
            bat 'docker system prune -f --volumes || echo "Docker cleanup failed, but continuing..."'
          } catch (Exception e) {
            echo 'Error in always post action: ' + e.toString()
          }
        }
      }
    }
    success {
      node('built-in') {
        script {
          if (env.BRANCH_NAME == 'main') {
            echo 'Pipeline succeeded!'
          }
        }
      }
    }
    failure {
      node('built-in') {
        script {
          try {
            echo 'Pipeline failed!'
            archiveArtifacts artifacts: '**/test-results/**/*.xml', allowEmptyArchive: true
            archiveArtifacts artifacts: '**/coverage.xml', allowEmptyArchive: true
          } catch (Exception e) {
            echo 'Error in failure handling: ' + e.toString()
          }
        }
      }
    }
    cleanup {
      node('built-in') {
        script {
          try {
            if (fileExists('docker-compose.yml')) {
              bat 'docker-compose down --remove-orphans || echo "No containers to stop"'
            } else {
              echo 'No docker-compose.yml found, skipping container cleanup'
            }
            bat 'docker system prune -f --volumes || echo "No Docker resources to clean"'
          } catch (Exception e) {
            echo 'Warning: Error during Docker cleanup: ' + e.message
          }
        }
      }
    }
  }
}
