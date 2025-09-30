## ⚙️ Configuring the Jenkins CI/CD Pipeline

This guide details how to set up a Jenkins Pipeline job for the Appointment Management Service, assuming you have a local Jenkins instance already running. This pipeline will automate the build, test, and Docker image creation process.

### Prerequisites

*   **Running Jenkins Instance**: Ensure your local Jenkins server is up and accessible (e.g., `http://localhost:8080`).
*   **Git SCM Plugin**: Ensure the Git plugin is installed in Jenkins (`Manage Jenkins -> Plugins -> Available Plugins`).
*   **HTML Publisher Plugin**: For publishing coverage reports (`Manage Jenkins -> Plugins -> Available Plugins`).
*   **Docker & Docker Compose**: Docker Desktop must be running on the machine where Jenkins agent executes builds (often the same machine as Jenkins for local setups).

### Step 1: Create a New Jenkins Pipeline Job

1.  **Log in to Jenkins**: Open your Jenkins dashboard (e.g., `http://localhost:8080`).
2.  **Click "New Item"**: On the left-hand navigation, select "New Item".
3.  **Enter Item Name**: Give your project a descriptive name, e.g., `appointment-service-ci`.
4.  **Select "Pipeline"**: Choose "Pipeline" as the project type.
5.  **Click "OK"**.

### Step 2: Configure Global Credentials (Highly Recommended for Secrets)

For sensitive information (like database passwords and `SECRET_KEY`), it's best practice to store them as Jenkins credentials rather than directly in the `Jenkinsfile` or as plain text environment variables.

1.  **Go to "Manage Jenkins" -> "Manage Credentials" -> "Jenkins" -> "Global credentials (unrestricted)".**
2.  **Click "Add Credentials".**
3.  **For each sensitive variable (e.g., `MYSQL_ROOT_PASSWORD`, `MYSQL_PASSWORD`, `SECRET_KEY`):**
    *   **Kind**: "Secret text"
    *   **Scope**: "Global"
    *   **Secret**: Paste the actual secret value from your `.env` file (e.g., `rootsecret`, `appsecret`, `change-me-in-production`).
    *   **ID**: Give it a clear ID, matching the variable name (e.g., `MYSQL_ROOT_PASSWORD_CRED`, `MYSQL_PASSWORD_CRED`, `SECRET_KEY_CRED`).
    *   **Description**: Optional, but good for clarity (e.g., "MySQL Root Password for Test DB").
    *   Click "Create".

    **Example Credentials to Create:**
    *   `ID: MYSQL_ROOT_PASSWORD_CRED` (Secret: your `MYSQL_ROOT_PASSWORD`)
    *   `ID: MYSQL_PASSWORD_CRED` (Secret: your `MYSQL_PASSWORD`)
    *   `ID: SECRET_KEY_CRED` (Secret: your `SECRET_KEY`)
    *   `ID: GITHUB_REPO_CRED` (If your GitHub repo is private and requires authentication, use "Username with password" credential type for your GitHub username and Personal Access Token)

    *(Note: For `TEST_DATABASE_URL`, `MYSQL_USER`, `MYSQL_DATABASE`, `APP_NAME`, `ENVIRONMENT`, `DEBUG`, `PORT`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `ALLOW_ORIGINS`, `ALLOW_METHODS`, `ALLOW_HEADERS`, you can pass these directly as environment variables in the Jenkins job configuration as they are not as sensitive or are expected to be known/default.)*

### Step 3: Configure the Pipeline Job

1.  **Go back to your `appointment-service-ci` job configuration.**
2.  **General Tab:**
    *   Check "Discard old builds" if you want to limit build history.
3.  **Pipeline Tab:**
    *   **Definition**: Select "Pipeline script from SCM".
    *   **SCM**: Select "Git".
        *   **Repository URL**: Enter your project's Git repository URL (e.g., `https://github.com/yahyaa19/cmd-appointment.git`).
        *   **Credentials**: If your repository is private, select the `GITHUB_REPO_CRED` you created. If public, leave it as `- none -`.
        *   **Branches to build**: `*/main` (or whichever branch you want to trigger CI on).
        *   **Script Path**: `Jenkinsfile` (This is the default, ensure it matches your file name).

4.  **Environment Variables (for non-secret values):**
    You can define additional environment variables here to pass into your pipeline. These will be accessible within the `Jenkinsfile`.

    *   Under "Pipeline" section, check "Prepare an environment for the run" and click "Add".
    *   Choose "Secret text" for sensitive variables or "Text" for non-sensitive ones.
    *   **Example (for `TEST_DATABASE_URL`):**
        *   **Kind**: "Secret text" (if you want to hide it in logs) or "Text"
        *   **Variable**: `TEST_DATABASE_URL`
        *   **Value**: `mysql+pymysql://appuser:appsecret@mysql:3306/appointment_test_db?charset=utf8mb4`
            *(Note: While `appsecret` is in the URL, for the test database context, it's often considered less sensitive than production credentials. For absolute maximum security, you could extract all parts of this URL into separate credentials too.)*

    **Best Practice with Credentials:**
    Instead of passing the full `TEST_DATABASE_URL` as a text variable, you can use the credentials you set up in Step 2 within your `Jenkinsfile`. This is the most secure approach. You would add `withCredentials` blocks in your `Jenkinsfile` like this:

    ```groovy
    // Example in Jenkinsfile (DO NOT EDIT HERE)
    stage('Integration Tests') {
      steps {
        script {
          withCredentials([string(credentialsId: 'MYSQL_PASSWORD_CRED', variable: 'MYSQL_PASSWORD_VAR'),
                           string(credentialsId: 'MYSQL_ROOT_PASSWORD_CRED', variable: 'MYSQL_ROOT_PASSWORD_VAR'),
                           string(credentialsId: 'SECRET_KEY_CRED', variable: 'SECRET_KEY_VAR')]) {
            // Now you can use ${env.MYSQL_PASSWORD_VAR}, ${env.MYSQL_ROOT_PASSWORD_VAR}, etc.
            // Construct the DATABASE_URL using these variables and other non-secret env vars.
            // Example:
            // def test_db_url = "mysql+pymysql://${env.MYSQL_USER}:${env.MYSQL_PASSWORD_VAR}@mysql:3306/${env.MYSQL_DATABASE}?charset=utf8mb4"
            // withEnv(["DATABASE_URL=${test_db_url}"]) {
            //   bat 'docker-compose -f docker-compose.test.yml up -d --build --wait'
            //   bat "${PYTHON} -m pytest tests/integration \\
            //     -v \\
            //     --junitxml=test-results/integration-tests.xml"
            // }
          }
        }
      }
    }
    ```
    *(For simplicity in the initial setup, we kept `TEST_DATABASE_URL` directly in `withEnv` in the `Jenkinsfile`, but for enterprise-grade security, integrating credentials is key.)*

5.  **Build Triggers:**
    *   **Poll SCM**: If you want Jenkins to regularly check your Git repository for new commits. Set a schedule (e.g., `H/5 * * * *` to check every 5 minutes).
    *   **GitHub hook trigger for GITScm polling**: This is generally preferred for immediate builds after a push. You'll need to configure a webhook in your GitHub repository settings pointing to your Jenkins URL (`http://your-jenkins-url/github-webhook/`).

6.  **Post-build Actions:**
    The `Jenkinsfile` already defines `junit` and `publishHTML` actions, so you typically don't need to configure more here unless you have additional reporting needs.

7.  **Click "Save"**.

### Step 4: Run Your First Build

1.  **Go to your pipeline job dashboard.**
2.  **Click "Build Now"** on the left-hand side.
3.  Monitor the "Console Output" for progress and any errors.

### Step 5: Review Build Results

After the build completes:

*   **Console Output**: Check for errors or warnings.
*   **Test Result Trend**: See the number of passed/failed tests.
*   **Coverage Report**: Access your HTML coverage report if the `publishHTML` step was successful.

### Troubleshooting Tips

*   **"Access denied for user..."**: Ensure your `MYSQL_USER` and `MYSQL_PASSWORD` are correctly set in the Jenkins environment variables (or credentials) and match what MySQL expects.
*   **"No working Python installation found..."**: Ensure the Jenkins agent has Python 3.11+ installed and accessible in its PATH, or that the `pythonPaths` list in the `Jenkinsfile` correctly points to an existing Python executable.
*   **`docker-compose` command not found**: Ensure Docker Desktop is installed and running on the Jenkins agent machine, and that Docker's executables are in the system's PATH.
*   **Network issues in Docker Compose**: If services can't communicate (e.g., `app` can't reach `db`), double-check service names and ports in `docker-compose.yml` and `Jenkinsfile`.
*   **Jenkins agent permissions**: Ensure the Jenkins user has necessary permissions to execute Docker commands and access the workspace.

By following these steps, you should be able to configure their Jenkins job to run the CI/CD pipeline, automating the entire testing and Docker image build process.