"""Service for auto-generating README.md files for exported projects."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.db.models import Project


class ReadmeGenerator:
    """Generates professional README.md files for projects."""

    def generate(
        self,
        project: Project,
        tech_stack: List[str],
        documentation_level: str = "standard",
    ) -> str:
        """Generate README.md content for a project.

        Args:
            project: Project data
            tech_stack: List of detected technologies
            documentation_level: 'minimal', 'standard', or 'comprehensive'

        Returns:
            README.md content as string
        """
        readme_parts = [
            self._generate_title(project),
            "",
            self._generate_description(project),
            "",
        ]

        if tech_stack:
            readme_parts.extend([
                self._generate_tech_stack_section(tech_stack),
                "",
            ])

        readme_parts.extend([
            self._generate_prerequisites_section(tech_stack),
            "",
            self._generate_setup_section(tech_stack, documentation_level),
            "",
        ])

        if documentation_level in ["standard", "comprehensive"]:
            readme_parts.extend([
                self._generate_structure_section(),
                "",
                self._generate_available_scripts_section(tech_stack),
                "",
                self._generate_testing_section(),
                "",
            ])

        if documentation_level == "comprehensive":
            readme_parts.extend([
                self._generate_deployment_section(),
                "",
                self._generate_contributing_section(),
                "",
            ])

        readme_parts.extend([
            self._generate_footer(project),
        ])

        return "\n".join(readme_parts)

    def _generate_title(self, project: Project) -> str:
        """Generate title section."""
        return f"# {project.name}\n\n**Status:** {self._format_status(project.status)}\n**Priority:** {self._format_priority(project.priority)}"

    def _generate_description(self, project: Project) -> str:
        """Generate description section."""
        if project.description:
            return f"{project.description}"
        return "A project exported from Deviant - AI Agent Project Management System."

    def _generate_tech_stack_section(self, tech_stack: List[str]) -> str:
        """Generate technology stack section."""
        tech_list = ", ".join(tech_stack)
        return f"## Technology Stack\n\n{tech_list}"

    def _generate_prerequisites_section(self, tech_stack: List[str]) -> str:
        """Generate prerequisites section."""
        prereqs = []

        if any(t in tech_stack for t in ["nodejs", "react", "next.js"]):
            prereqs.append("- **Node.js:** 16.x or higher")
            prereqs.append("- **npm** or **yarn** package manager")

        if "python" in tech_stack:
            prereqs.append("- **Python:** 3.8 or higher")
            prereqs.append("- **pip** package manager")

        if "docker" in tech_stack:
            prereqs.append("- **Docker:** 20.x or higher")
            prereqs.append("- **Docker Compose:** 1.29 or higher")

        if not prereqs:
            prereqs = [
                "- Check the specific setup section for your framework/language"
            ]

        return f"## Prerequisites\n\n" + "\n".join(prereqs)

    def _generate_setup_section(self, tech_stack: List[str], documentation_level: str) -> str:
        """Generate setup/installation section."""
        setup_steps = ["## Setup & Installation\n\n### 1. Extract the Project\n\n```bash\nunzip project_name.zip\ncd project_name\n```"]

        if "docker" in tech_stack:
            setup_steps.append(
                "\n### 2. Using Docker\n\n```bash\ndocker-compose up\n```"
            )
            if documentation_level == "comprehensive":
                setup_steps.append(
                    "\nThe application will be available at `http://localhost:3000`"
                )
        else:
            setup_steps.append("\n### 2. Install Dependencies\n")

            if any(t in tech_stack for t in ["nodejs", "react", "next.js"]):
                setup_steps.append(
                    "\n```bash\nnpm install\n# or\nyarn install\n```"
                )
            elif "python" in tech_stack:
                setup_steps.append(
                    "\n```bash\npip install -r requirements.txt\n```"
                )

            setup_steps.append(
                "\n### 3. Environment Configuration\n\n"
                "Copy `.env.example` to `.env` and configure the required environment variables:\n\n"
                "```bash\ncp .env.example .env\n# Edit .env with your configuration\n```"
            )

            setup_steps.append("\n### 4. Run the Project\n")

            if any(t in tech_stack for t in ["nodejs", "react", "next.js"]):
                setup_steps.append(
                    "\n```bash\nnpm run dev\n# or\nyarn dev\n```"
                )
            elif "python" in tech_stack:
                setup_steps.append(
                    "\n```bash\npython main.py\n# or for Flask/Django\npython manage.py runserver\n```"
                )

        return "".join(setup_steps)

    def _generate_structure_section(self) -> str:
        """Generate project structure section."""
        return """## Project Structure

```
.
├── README.md              # This file
├── .gitignore            # Git ignore rules
├── .env.example          # Environment variables template
├── package.json          # Dependencies (for Node.js projects)
├── requirements.txt      # Dependencies (for Python projects)
├── src/                  # Source code
│   ├── index.js         # Application entry point
│   └── ...              # Additional source files
├── public/              # Static assets
│   ├── index.html
│   └── ...
├── tests/               # Test files
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/                # Documentation
│   ├── API.md
│   ├── ARCHITECTURE.md
│   └── ...
└── Deviant/             # Deviant project metadata
    ├── project_info.json
    └── tasks.json
```"""

    def _generate_available_scripts_section(self, tech_stack: List[str]) -> str:
        """Generate available scripts section."""
        scripts = ["## Available Scripts\n"]

        if any(t in tech_stack for t in ["nodejs", "react", "next.js"]):
            scripts.append(
                "\n### Development\n\n```bash\nnpm run dev    # Start development server\n```\n\n"
                "### Production\n\n```bash\nnpm run build  # Build for production\nnpm start      # Start production server\n```\n\n"
                "### Testing\n\n```bash\nnpm test       # Run tests\nnpm run test:coverage  # Run tests with coverage\n```"
            )
        elif "python" in tech_stack:
            scripts.append(
                "\n### Running the Application\n\n```bash\npython main.py\n```\n\n"
                "### Running Tests\n\n```bash\npytest\npytest --cov  # With coverage\n```"
            )

        return "".join(scripts)

    def _generate_testing_section(self) -> str:
        """Generate testing section."""
        return """## Testing

Run the test suite:

```bash
# Run all tests
npm test          # For Node.js projects
pytest            # For Python projects

# Run specific test file
npm test -- MyTest.test.js
pytest tests/test_module.py

# Run with coverage
npm run test:coverage
pytest --cov
```"""

    def _generate_deployment_section(self) -> str:
        """Generate deployment section."""
        return """## Deployment

This project can be deployed to various platforms:

### Vercel (Recommended for Next.js/React)

1. Push your code to GitHub
2. Connect your GitHub repository to Vercel
3. Vercel will auto-deploy on every push
4. Set environment variables in Vercel dashboard

### Docker

```bash
docker build -t project-name .
docker run -p 3000:3000 project-name
```

### Other Platforms

- **Netlify** - Great for static sites and JAMstack
- **Heroku** - Good for backend services
- **AWS/Azure/GCP** - Full cloud deployment options

See the `docs/DEPLOYMENT.md` file for detailed instructions."""

    def _generate_contributing_section(self) -> str:
        """Generate contributing section."""
        return """## Contributing

Contributions are welcome! Please follow these steps:

1. Create a feature branch (`git checkout -b feature/AmazingFeature`)
2. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
3. Push to the branch (`git push origin feature/AmazingFeature`)
4. Open a Pull Request

Please ensure:
- Code follows the project's style guide
- All tests pass
- New features include tests
- Documentation is updated"""

    def _generate_footer(self, project: Project) -> str:
        """Generate footer section."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        return f"""## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Generated by [Deviant](https://github.com/anthropics/Deviant)** on {timestamp}

This project was created by AI agents working collaboratively. For more information about the project, see `Deviant/project_info.json`."""

    def _format_status(self, status: Any) -> str:
        """Format project status for display."""
        if hasattr(status, 'value'):
            return status.value
        return str(status)

    def _format_priority(self, priority: Any) -> str:
        """Format priority for display."""
        if hasattr(priority, 'value'):
            priority_value = priority.value
        else:
            priority_value = str(priority)

        # Capitalize first letter
        return priority_value.capitalize()
