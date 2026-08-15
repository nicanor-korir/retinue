"""Service for generating PDF exports using Playwright."""
from typing import Dict, Any, Optional
from pathlib import Path
import tempfile
import asyncio
from datetime import datetime
import json

from jinja2 import Environment, FileSystemLoader
import logging

logger = logging.getLogger(__name__)


class PDFGenerationService:
    """Generate professional PDFs from HTML templates."""

    def __init__(self, templates_dir: Optional[Path] = None):
        """Initialize PDF generation service.

        Args:
            templates_dir: Path to HTML templates directory
        """
        if templates_dir is None:
            templates_dir = Path(__file__).parent.parent / "templates" / "pdf"

        self.templates_dir = templates_dir
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True
        )

        self.env.filters['json'] = json.dumps
        self.env.filters['datetime'] = self._format_datetime

    def _format_datetime(self, dt: datetime, fmt: str = "%B %d, %Y") -> str:
        """Format datetime for display."""
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt)
        return dt.strftime(fmt)

    async def generate_project_summary_pdf(
        self,
        data: Dict[str, Any],
        output_path: Path,
        styling: Optional[Dict[str, Any]] = None
    ) -> Path:
        """Generate project summary PDF."""
        html_content = await self._render_template(
            "project_summary.html",
            data,
            styling or {}
        )
        return await self._html_to_pdf(html_content, output_path)

    async def generate_full_documentation_pdf(
        self,
        data: Dict[str, Any],
        output_path: Path,
        styling: Optional[Dict[str, Any]] = None
    ) -> Path:
        """Generate full documentation PDF."""
        html_content = await self._render_template(
            "full_documentation.html",
            data,
            styling or {}
        )
        return await self._html_to_pdf(html_content, output_path)

    async def generate_task_report_pdf(
        self,
        data: Dict[str, Any],
        output_path: Path,
        styling: Optional[Dict[str, Any]] = None
    ) -> Path:
        """Generate task report PDF."""
        html_content = await self._render_template(
            "task_report.html",
            data,
            styling or {}
        )
        return await self._html_to_pdf(html_content, output_path)

    async def generate_agent_activity_report_pdf(
        self,
        data: Dict[str, Any],
        output_path: Path,
        styling: Optional[Dict[str, Any]] = None
    ) -> Path:
        """Generate agent activity report PDF."""
        html_content = await self._render_template(
            "agent_activity_report.html",
            data,
            styling or {}
        )
        return await self._html_to_pdf(html_content, output_path)

    async def generate_code_documentation_pdf(
        self,
        data: Dict[str, Any],
        output_path: Path,
        styling: Optional[Dict[str, Any]] = None
    ) -> Path:
        """Generate code documentation PDF."""
        html_content = await self._render_template(
            "code_documentation.html",
            data,
            styling or {}
        )
        return await self._html_to_pdf(html_content, output_path)

    async def generate_analytics_metrics_pdf(
        self,
        data: Dict[str, Any],
        output_path: Path,
        styling: Optional[Dict[str, Any]] = None
    ) -> Path:
        """Generate analytics and metrics PDF."""
        html_content = await self._render_template(
            "analytics_metrics.html",
            data,
            styling or {}
        )
        return await self._html_to_pdf(html_content, output_path)

    async def _render_template(
        self,
        template_name: str,
        data: Dict[str, Any],
        styling: Dict[str, Any]
    ) -> str:
        """Render HTML template with data.

        Args:
            template_name: Name of the template file
            data: Data to render
            styling: Styling options (colors, fonts, etc.)

        Returns:
            Rendered HTML string
        """
        try:
            template = self.env.get_template(template_name)

            # Add styling to context
            context = {
                **data,
                "styling": self._get_default_styling() | styling,
                "generated_at": datetime.now(),
            }

            html = template.render(context)
            return html

        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            raise

    def _get_default_styling(self) -> Dict[str, Any]:
        """Get default styling configuration."""
        return {
            "primary_color": "#2563eb",
            "secondary_color": "#64748b",
            "accent_color": "#f59e0b",
            "font_family": "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
            "code_font": "Fira Code, Menlo, Monaco, Courier New, monospace",
            "font_size_base": "11pt",
            "font_size_h1": "24pt",
            "font_size_h2": "18pt",
            "font_size_h3": "14pt",
            "line_height": "1.6",
            "page_size": "A4",
            "margins": {"top": "1in", "right": "0.75in", "bottom": "1in", "left": "0.75in"},
        }

    async def _html_to_pdf(self, html_content: str, output_path: Path) -> Path:
        """Convert HTML to PDF using Playwright (sync method for Windows compatibility).

        Args:
            html_content: HTML content to convert
            output_path: Path where PDF should be saved

        Returns:
            Path to generated PDF
        """
        try:
            # Use synchronous Playwright instead of async to avoid Windows subprocess issues
            from playwright.sync_api import sync_playwright
            import threading

            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Flag to store any exception from thread
            error_holder = {"error": None}

            def run_playwright():
                """Run Playwright in a separate thread to avoid asyncio subprocess issues on Windows."""
                try:
                    with sync_playwright() as p:
                        browser = p.chromium.launch(headless=True)
                        context = browser.new_context()
                        page = context.new_page()

                        # Set content and wait for images/fonts to load
                        page.set_content(html_content, wait_until="networkidle")

                        # Generate PDF with professional settings
                        page.pdf(
                            path=str(output_path),
                            format="A4",
                            margin={
                                "top": "1in",
                                "right": "0.75in",
                                "bottom": "1in",
                                "left": "0.75in"
                            },
                            print_background=True,
                            prefer_css_page_size=True,
                        )

                        context.close()
                        browser.close()

                except Exception as e:
                    error_holder["error"] = e

            # Run Playwright in a thread (avoids asyncio subprocess issues on Windows)
            thread = threading.Thread(target=run_playwright, daemon=False)
            thread.start()
            thread.join(timeout=60)  # Wait up to 60 seconds

            if error_holder["error"]:
                raise error_holder["error"]

            if thread.is_alive():
                logger.error("PDF generation timed out after 60 seconds")
                raise TimeoutError("PDF generation timed out")

            logger.info(f"PDF generated successfully: {output_path}")
            return output_path

        except ImportError:
            logger.error("Playwright not installed. Install with: pip install playwright")
            raise
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            raise


class PDFTemplateBuilder:
    """Builder class to help create professional PDF templates."""

    @staticmethod
    def create_header(title: str, subtitle: Optional[str] = None) -> str:
        """Create a professional header section."""
        return f"""
        <div class="header">
            <h1>{title}</h1>
            {f'<h2>{subtitle}</h2>' if subtitle else ''}
            <div class="generated-info">
                Generated on {datetime.now().strftime('%B %d, %Y')}
            </div>
        </div>
        """

    @staticmethod
    def create_table_of_contents(sections: list) -> str:
        """Create a table of contents."""
        items = "\n".join([f'<li><a href="#{s["id"]}">{s["title"]}</a></li>' for s in sections])
        return f"""
        <div class="toc">
            <h2>Table of Contents</h2>
            <ul>{items}</ul>
        </div>
        """

    @staticmethod
    def create_section(section_id: str, title: str, content: str) -> str:
        """Create a document section."""
        return f"""
        <section id="{section_id}">
            <h2>{title}</h2>
            <div class="section-content">
                {content}
            </div>
        </section>
        """

    @staticmethod
    def create_code_block(code: str, language: str = "python") -> str:
        """Create a syntax-highlighted code block."""
        # Use Pygments for syntax highlighting
        try:
            from pygments import highlight
            from pygments.lexers import get_lexer_by_name
            from pygments.formatters import HtmlFormatter

            lexer = get_lexer_by_name(language)
            formatter = HtmlFormatter(style="monokai", linenos=True)
            highlighted = highlight(code, lexer, formatter)
            return f'<div class="code-block">{highlighted}</div>'
        except:
            # Fallback to plain code block
            return f'<pre><code class="language-{language}">{code}</code></pre>'

    @staticmethod
    def create_metrics_grid(metrics: Dict[str, Any]) -> str:
        """Create a metrics grid display."""
        items = "".join([
            f'<div class="metric-card"><div class="metric-value">{v}</div><div class="metric-label">{k}</div></div>'
            for k, v in metrics.items()
        ])
        return f'<div class="metrics-grid">{items}</div>'
