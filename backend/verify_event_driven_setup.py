#!/usr/bin/env python3
"""
Verification script to ensure all agents are properly configured for event-driven execution
"""

import sys
from pathlib import Path

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_file(filepath, checks):
    """Check a file for required content"""
    print(f"\n{BLUE}Checking {filepath.name}...{RESET}")

    if not filepath.exists():
        print(f"  {RED}✗ File not found{RESET}")
        return False

    with open(filepath, 'r') as f:
        content = f.read()

    all_passed = True
    for check_name, search_string in checks.items():
        if search_string in content:
            print(f"  {GREEN}✓{RESET} {check_name}")
        else:
            print(f"  {RED}✗{RESET} {check_name} - Missing: {search_string}")
            all_passed = False

    return all_passed

def main():
    base_path = Path(__file__).parent

    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Event-Driven Setup Verification{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

    all_checks_passed = True

    # Check main.py
    main_checks = {
        "Event-driven imports": "from app.services.event_driven_integration import",
        "Specialized handlers import": "from app.agents.specialized_event_handlers import setup_specialized_handlers",
        "Initialize event-driven system": "await initialize_event_driven_system()",
        "Start event-driven services": "await start_event_driven_services()",
        "Shutdown event-driven system": "await shutdown_event_driven_system()",
        "Use start_agent()": "await start_agent(agent)",
        "Setup specialized handlers": "setup_specialized_handlers(",
    }
    all_checks_passed &= check_file(base_path / "app/main.py", main_checks)

    # Check each agent
    agent_files = [
        "app/agents/ceo_agent.py",
        "app/agents/cto_agent.py",
        "app/agents/pm_agent.py",
        "app/agents/hr_agent.py",
        "app/agents/backend_engineer_agent.py",
        "app/agents/frontend_engineer_agent.py",
        "app/agents/designer_agent.py",
    ]

    for agent_file in agent_files:
        agent_checks = {
            "EventDrivenMixin import": "from app.agents.event_driven_mixin import EventDrivenMixin",
            "EventDrivenMixin in class": "EventDrivenMixin):",
            "setup_event_listeners() call": "self.setup_event_listeners()",
        }
        all_checks_passed &= check_file(base_path / agent_file, agent_checks)

    # Summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    if all_checks_passed:
        print(f"{GREEN}✅ All checks passed! Event-driven system is properly configured.{RESET}")
        print(f"\n{YELLOW}Next steps:{RESET}")
        print(f"  1. Start the backend: uvicorn app.main:app --reload")
        print(f"  2. Look for event-driven initialization messages in logs")
        print(f"  3. Test with: POST /api/v1/projects")
        print(f"  4. Agents should respond in <1 second (not 15 minutes!)")
        return 0
    else:
        print(f"{RED}❌ Some checks failed. Please review the errors above.{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
