## Getting Started: Setting Up Your Development Environment

This guide will walk you through setting up the Appointment Management Service for local development, testing, and understanding its CI/CD integration.

### Prerequisites

Before you begin, ensure you have the following installed on your machine:

1.  **Git**: For cloning the repository.
    *   [Download Git](https://git-scm.com/downloads)
2.  **Docker Desktop** (includes Docker Engine and Docker Compose): For running the application and database in containers.
    *   [Download Docker Desktop](https://www.docker.com/products/docker-desktop)
    *   Ensure Docker Desktop is running before proceeding.

### Step 1: Clone the Repository

Open your terminal or command prompt and clone the project:

```bash
git clone https://github.com/yahyaa19/cmd-appointment.git
cd cmd-appointment
```


### Step 2: Create and Configure the `.env` File

This project uses environment variables to manage sensitive configurations (like database credentials) securely. You **must** create a `.env` file.

1.  **Create the `.env` file:**
    Copy the provided example environment file to create your own:
    ```bash
    # On Windows
    copy .env.example .env

    # On macOS/Linux
    cp .env.example .env
    ```



### Step 3: Run the Application Locally with Docker Compose

This will build your Docker images and start the FastAPI application, MySQL database, and Adminer for database management.

1.  **Build and Start Services:**
    From the project root, run:
    ```bash
    docker-compose up --build -d
    ```
    *   `--build`: Rebuilds the Docker images (useful when you make code changes).
    *   `-d`: Runs containers in detached mode (in the background).

2.  **Verify Services:**
    Check if the containers are running:
    ```bash
    docker-compose ps
    ```
    You should see `app`, `db`, and `adminer` services listed as `Up`.

3.  **Access the Application:**
    Once the application is running, you can access:
    *   **FastAPI Documentation (Swagger UI)**: `http://localhost:8007/docs`
    *   **FastAPI Alternative Docs (ReDoc)**: `http://localhost:8007/redoc`
    *   **Adminer (Database GUI)**: `http://localhost:8081`
        *   **Adminer Login:**
            *   System: `MySQL`
            *   Server: `db` (This is the name of your MySQL service within the Docker network)
            *   Username: `appuser` (from your `.env`)
            *   Password: `appsecret` (from your `.env`)
            *   Database: `appointment_db` (from your `.env`)

### Step 4: Run Database Migrations (Manual - if needed)

The application attempts to create tables on startup. However, if you make schema changes (e.g., add new models) and need to apply them or manage database versions, you'll use Alembic.

1.  **Generate a new migration script (if schema changes were made):**
    ```bash
    docker-compose exec app alembic revision --autogenerate -m "Add description of your changes"
    ```
2.  **Apply migrations to the running database:**
    ```bash
    docker-compose exec app alembic upgrade head
    ```

<!-- ### Step 5: Run Automated Tests Locally

A dedicated Docker Compose file (`docker-compose.test.yml`) is provided for running tests in an isolated database environment.

1.  **Run the test suite:**
    ```bash
    docker-compose -f docker-compose.test.yml up --build --exit-code-from test
    ```
    *   This command will:
        *   Build the `test` service image (using `Dockerfile.test`).
        *   Spin up a separate MySQL container (`mysql` service in `docker-compose.test.yml`).
        *   Automatically apply Alembic migrations to this test database via `tests/conftest.py`.
        *   Execute all `pytest` tests.
        *   Exit with the test suite's exit code, indicating success or failure.
        *   Automatically shut down the test containers after execution. -->

<!-- ### Step 5: MySQL Workbench Connection Details

If you wish to connect to your *local development* MySQL database using MySQL Workbench (or any other external client), use these details:

*   **Hostname**: `127.0.0.1` or `localhost`
*   **Port**: `3307` (This is the port mapped from the container to your host machine in `docker-compose.yml`)
*   **Username**: `appuser` (from your `.env` file)
*   **Password**: `appsecret` (from your `.env` file)
*   **Default Schema (Database)**: `appointment_db` (from your `.env` file) -->

### Step 5: Jenkins CI/CD Pipeline (for Automation)

The `Jenkinsfile` in the root of the repository defines the CI/CD pipeline. Once your code is pushed to the `main` branch, a Jenkins job configured to monitor this repository will automatically:

1.  **Checkout** the code.
2.  **Set up a Python environment** and install dependencies.
3.  Run **Code Quality & Linting** checks (Flake8, Black, Isort).
4.  Perform **Security Scanning** (Bandit, Safety).
5.  Execute **Unit Tests**.
6.  Execute **Integration Tests** against a dedicated MySQL test database (managed by `docker-compose.test.yml`).
7.  **Build a Docker Image** of the application.

*   **Note for Jenkins Setup:** When configuring your Jenkins job, you'll need to ensure that the environment variables (especially `TEST_DATABASE_URL`, `MYSQL_USER`, `MYSQL_PASSWORD`, etc., from your `.env` template) are securely passed to the Jenkins build environment. This is typically done through Jenkins's "Global properties," "Credentials," or `withEnv` blocks within the pipeline script, depending on your Jenkins setup.