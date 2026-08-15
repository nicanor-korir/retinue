"""Service for generating .env.example files from project configuration."""
from typing import Optional, Dict, Any
from app.db.models import Project


class EnvExampleGenerator:
    """Generates .env.example files for projects."""

    COMMON_ENV_VARS = [
        ("NODE_ENV", "production", "Environment (development, staging, production)"),
        ("DEBUG", "false", "Enable debug mode"),
        ("LOG_LEVEL", "info", "Logging level (debug, info, warn, error)"),
    ]

    FRAMEWORK_ENV_VARS = {
        "nodejs": [
            ("PORT", "3000", "Server port"),
            ("HOST", "localhost", "Server host"),
        ],
        "react": [
            ("REACT_APP_API_URL", "http://localhost:3000/api", "API base URL"),
        ],
        "next.js": [
            ("NEXT_PUBLIC_API_URL", "http://localhost:3000/api", "Public API URL"),
            ("API_SECRET_KEY", "", "Secret key for API"),
        ],
        "python": [
            ("FLASK_ENV", "production", "Flask environment"),
            ("FLASK_APP", "app.py", "Flask app file"),
            ("DATABASE_URL", "postgresql://user:password@localhost/dbname", "Database URL"),
        ],
        "django": [
            ("DEBUG", "False", "Django debug mode"),
            ("SECRET_KEY", "", "Django secret key"),
            ("ALLOWED_HOSTS", "localhost,127.0.0.1", "Allowed hosts"),
            ("DATABASE_URL", "postgresql://user:password@localhost/dbname", "Database connection string"),
        ],
        "fastapi": [
            ("FASTAPI_ENV", "production", "FastAPI environment"),
            ("DATABASE_URL", "postgresql://user:password@localhost/dbname", "Database URL"),
            ("REDIS_URL", "redis://localhost:6379", "Redis connection URL"),
        ],
    }

    DATABASE_ENV_VARS = {
        "postgresql": [
            ("DATABASE_URL", "postgresql://user:password@localhost:5432/dbname", "PostgreSQL connection URL"),
            ("DB_HOST", "localhost", "Database host"),
            ("DB_PORT", "5432", "Database port"),
            ("DB_NAME", "myapp", "Database name"),
            ("DB_USER", "postgres", "Database user"),
            ("DB_PASSWORD", "", "Database password"),
        ],
        "mongodb": [
            ("MONGODB_URI", "mongodb://localhost:27017", "MongoDB connection URI"),
            ("MONGODB_DB", "myapp", "MongoDB database name"),
        ],
        "redis": [
            ("REDIS_URL", "redis://localhost:6379", "Redis connection URL"),
            ("REDIS_PASSWORD", "", "Redis password"),
        ],
    }

    THIRD_PARTY_VARS = {
        "stripe": [
            ("STRIPE_PUBLIC_KEY", "", "Stripe publishable key"),
            ("STRIPE_SECRET_KEY", "", "Stripe secret key"),
        ],
        "sendgrid": [
            ("SENDGRID_API_KEY", "", "SendGrid API key"),
            ("SENDGRID_FROM_EMAIL", "noreply@example.com", "From email address"),
        ],
        "auth0": [
            ("AUTH0_DOMAIN", "", "Auth0 domain"),
            ("AUTH0_CLIENT_ID", "", "Auth0 client ID"),
            ("AUTH0_CLIENT_SECRET", "", "Auth0 client secret"),
        ],
        "aws": [
            ("AWS_ACCESS_KEY_ID", "", "AWS access key"),
            ("AWS_SECRET_ACCESS_KEY", "", "AWS secret key"),
            ("AWS_REGION", "us-east-1", "AWS region"),
        ],
    }

    async def generate(self, project: Project) -> Optional[str]:
        """Generate .env.example content for a project.

        Args:
            project: Project data

        Returns:
            .env.example content as string, or None if no env vars needed
        """
        env_vars = []

        # Add header
        env_vars.append("# Environment Configuration")
        env_vars.append("# Copy this file to .env and fill in the required values")
        env_vars.append("")

        # Add common vars
        env_vars.append("# Common Configuration")
        for var_name, default_value, description in self.COMMON_ENV_VARS:
            env_vars.append(f"# {description}")
            env_vars.append(f"{var_name}={default_value}")
            env_vars.append("")

        # Detect frameworks and add framework-specific vars
        env_vars.append("# Application Configuration")
        tech_stack = await self._detect_tech_stack(project)

        for tech in tech_stack:
            if tech in self.FRAMEWORK_ENV_VARS:
                env_vars.append(f"\n# {tech.capitalize()} Configuration")
                for var_name, default_value, description in self.FRAMEWORK_ENV_VARS[tech]:
                    env_vars.append(f"# {description}")
                    env_vars.append(f"{var_name}={default_value}")
                    env_vars.append("")

        # Add database vars if detected
        db_vars = []
        for db_tech in self.DATABASE_ENV_VARS:
            if db_tech in tech_stack:
                db_vars.extend(self.DATABASE_ENV_VARS[db_tech])

        if db_vars:
            env_vars.append("\n# Database Configuration")
            for var_name, default_value, description in db_vars:
                env_vars.append(f"# {description}")
                env_vars.append(f"{var_name}={default_value}")
                env_vars.append("")

        # Add third-party service vars if detected in project metadata
        third_party_vars = []
        if project.meta_data:
            services = project.meta_data.get("integrations", {})
            for service in services:
                if service in self.THIRD_PARTY_VARS:
                    third_party_vars.extend(self.THIRD_PARTY_VARS[service])

        if third_party_vars:
            env_vars.append("\n# Third-Party Services")
            for var_name, default_value, description in third_party_vars:
                env_vars.append(f"# {description}")
                env_vars.append(f"{var_name}={default_value}")
                env_vars.append("")

        # Add footer note
        env_vars.append("\n# IMPORTANT: Never commit actual .env file with secrets to version control")
        env_vars.append("# Always use .env.example as a template")

        content = "\n".join(env_vars).strip()

        # Only return if we have more than just headers
        if len(content.split("\n")) > 5:
            return content

        return None

    async def _detect_tech_stack(self, project: Project) -> list[str]:
        """Detect technology stack from project metadata or tasks.

        Args:
            project: Project data

        Returns:
            List of detected technologies
        """
        tech_stack = set()

        # Check project metadata
        if project.meta_data:
            if "tech_stack" in project.meta_data:
                stack = project.meta_data.get("tech_stack", [])
                if isinstance(stack, list):
                    tech_stack.update(stack)

            if "frameworks" in project.meta_data:
                frameworks = project.meta_data.get("frameworks", [])
                if isinstance(frameworks, list):
                    tech_stack.update(frameworks)

        # Could extend to check tasks for mentions of technologies
        # For now, rely on metadata

        return list(tech_stack)
