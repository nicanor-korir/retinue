#!/usr/bin/env python3
"""
Script to update all agent files to include EventDrivenMixin
"""

import re
from pathlib import Path

# List of agent files to update
AGENT_FILES = [
    "app/agents/pm_agent.py",
    "app/agents/hr_agent.py",
    "app/agents/backend_engineer_agent.py",
    "app/agents/frontend_engineer_agent.py",
    "app/agents/designer_agent.py",
]

def update_agent_file(filepath):
    """Update a single agent file"""
    print(f"Updating {filepath}...")

    with open(filepath, 'r') as f:
        content = f.read()

    # Check if already updated
    if 'EventDrivenMixin' in content:
        print(f"  ✓ {filepath} already has EventDrivenMixin")
        return

    # 1. Add EventDrivenMixin import
    content = re.sub(
        r'(from app\.agents\.base_agent import BaseAgent)',
        r'\1\nfrom app.agents.event_driven_mixin import EventDrivenMixin',
        content
    )

    # 2. Add EventDrivenMixin to class definition
    content = re.sub(
        r'class (\w+Agent)\(BaseAgent\):',
        r'class \1(BaseAgent, EventDrivenMixin):',
        content
    )

    # 3. Add setup_event_listeners() after super().__init__()
    # Find the super().__init__() call and add listener setup after it
    pattern = r'(        super\(\).__init__\([^)]+\))\s*\n(\s{8}\))'
    replacement = r'\1\n\2\n\n        # Set up event-driven listeners\n        self.setup_event_listeners()'
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    # Write back
    with open(filepath, 'w') as f:
        f.write(content)

    print(f"  ✓ Updated {filepath}")

def main():
    base_path = Path(__file__).parent

    for agent_file in AGENT_FILES:
        filepath = base_path / agent_file
        if filepath.exists():
            update_agent_file(filepath)
        else:
            print(f"  ✗ File not found: {filepath}")

    print("\n✅ All agent files updated!")

if __name__ == "__main__":
    main()
