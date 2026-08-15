"""Service for generating .gitignore files based on tech stack."""
from typing import List


class GitignoreGenerator:
    """Generates .gitignore files for different tech stacks."""

    # Common patterns for all projects
    COMMON_PATTERNS = """
# IDE and Editor
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
Thumbs.db
*.sublime-project
*.sublime-workspace

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
desktop.ini

# Logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
lerna-debug.log*
.pnpm-debug.log*

# Environment
.env
.env.local
.env.*.local
.env.test
.env.production

# Build artifacts and caches
dist/
build/
*.min.js
*.min.css

# Temp files
tmp/
temp/
.cache
.tmp
""".strip()

    TECH_SPECIFIC = {
        "nodejs": """
# Node.js
node_modules/
npm-debug.log
yarn-lock
package-lock.json
*.tsbuildinfo
.npm
.eslintcache
.node_repl_history
*.tgz
""".strip(),

        "python": """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.dmypy.json
dmypy.json
.pyre/
*.pyc
.python-version
.venv
""".strip(),

        "react": """
# React / Create React App
node_modules/
.env.local
.env.development.local
.env.test.local
.env.production.local
npm-debug.log*
yarn-debug.log*
yarn-error.log*
build/
.env.build
""".strip(),

        "next.js": """
# Next.js
.next/
out/
*.pem
.next
.env.local
.env.development.local
.env.test.local
.env.production.local
npm-debug.log*
yarn-debug.log*
yarn-error.log*
""".strip(),

        "typescript": """
# TypeScript
*.tsbuildinfo
dist/
*.d.ts
""".strip(),

        "java": """
# Java
*.class
*.jar
*.war
*.ear
*.zip
*.tar.gz
target/
.gradle/
build/
.classpath
.project
.settings/
*.iml
.idea/
""".strip(),

        "ruby": """
# Ruby
*.gem
*.rbc
/.config
/coverage/
/InstalledFiles
/pkg/
/spec/reports/
/spec/tmp
/tmp/
/vendor/bundle/
/lib/bundler/man/
Gemfile.lock
""".strip(),

        "go": """
# Go
*.o
*.a
*.so
.DS_Store
dist/
vendor/
go.sum
""".strip(),

        "docker": """
# Docker
.dockerignore
docker-compose.override.yml
""".strip(),

        "rust": """
# Rust
/target/
Cargo.lock
**/*.rs.bk
""".strip(),

        "php": """
# PHP
composer.phar
/vendor/
.env
.env.*.local
/storage/
/bootstrap/cache/
""".strip(),

        "postgresql": """
# PostgreSQL
*.sql
pgdata/
postgres/
""".strip(),

        "mongodb": """
# MongoDB
data/
mongod.log
""".strip(),

        "redis": """
# Redis
*.rdb
dump.rdb
appendonly.aof
""".strip(),

        "kubernetes": """
# Kubernetes
*.yml.bak
*.yaml.bak
secrets/
""".strip(),
    }

    def generate(self, tech_stack: List[str]) -> str:
        """Generate .gitignore content for given tech stack.

        Args:
            tech_stack: List of technologies (e.g., ['nodejs', 'react', 'python'])

        Returns:
            .gitignore content as string
        """
        patterns = [self.COMMON_PATTERNS]

        # Add tech-specific patterns
        for tech in tech_stack:
            if tech in self.TECH_SPECIFIC:
                patterns.append(self.TECH_SPECIFIC[tech])

        # Join all patterns with blank lines between sections
        return "\n\n".join(patterns)
