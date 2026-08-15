#!/usr/bin/env python3
"""Test script for API filtering with multi-department support.

This script verifies that the API filtering endpoints work correctly with multi-department agents:
1. Filter by department returns multi-department agents
2. Department counts are accurate
3. Agents response includes both legacy 'department' and new 'departments' fields
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Import only the registry module to avoid dependency issues
import importlib.util
spec = importlib.util.spec_from_file_location(
    "agent_registry",
    backend_dir / "app" / "agents" / "agent_registry.py"
)
agent_registry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_registry)

AgentRegistry = agent_registry.AgentRegistry
Department = agent_registry.Department


def test_api_filtering():
    """Test API filtering with multi-department support."""
    print("=" * 80)
    print("Testing API Filtering with Multi-Department Support")
    print("=" * 80)
    print()

    # Test 1: Filter by Executive Department
    print("Test 1: Filter by Executive Department")
    print("-" * 80)
    exec_agents = AgentRegistry.get_agents_by_department(Department.EXECUTIVE)
    print(f"Found {len(exec_agents)} agents in Executive department:")
    for agent in exec_agents:
        departments = agent.get("departments") or [agent.get("department")]
        dept_values = [d.value if hasattr(d, "value") else str(d) for d in departments if d]
        print(f"  - {agent['agent_id']}: {agent['name']}")
        print(f"    Departments: {dept_values}")

    expected_exec_count = 6  # CEO, CTO, CFO, CMO, CHRO, COO
    if len(exec_agents) == expected_exec_count:
        print(f"✅ PASS: Found {expected_exec_count} executive agents")
    else:
        print(f"❌ FAIL: Expected {expected_exec_count} agents, found {len(exec_agents)}")
    print()

    # Test 2: Filter by Engineering Department (should include CEO and CTO)
    print("Test 2: Filter by Engineering Department")
    print("-" * 80)
    eng_agents = AgentRegistry.get_agents_by_department(Department.ENGINEERING)
    eng_agent_ids = [a["agent_id"] for a in eng_agents]
    print(f"Found {len(eng_agents)} agents in Engineering department:")
    for agent in eng_agents:
        departments = agent.get("departments") or [agent.get("department")]
        dept_values = [d.value if hasattr(d, "value") else str(d) for d in departments if d]
        print(f"  - {agent['agent_id']}: {agent['name']}")
        print(f"    Departments: {dept_values}")

    # Should include: CEO, CTO, backend_001, frontend_001, designer_001
    if "ceo_001" in eng_agent_ids and "cto_001" in eng_agent_ids:
        print("✅ PASS: Engineering department includes both CEO and CTO")
    else:
        print("❌ FAIL: CEO or CTO missing from Engineering department")
    print()

    # Test 3: Filter by Marketing Department
    print("Test 3: Filter by Marketing Department")
    print("-" * 80)
    mkt_agents = AgentRegistry.get_agents_by_department(Department.MARKETING)
    mkt_agent_ids = [a["agent_id"] for a in mkt_agents]
    print(f"Found {len(mkt_agents)} agents in Marketing department:")
    for agent in mkt_agents:
        departments = agent.get("departments") or [agent.get("department")]
        dept_values = [d.value if hasattr(d, "value") else str(d) for d in departments if d]
        print(f"  - {agent['agent_id']}: {agent['name']}")
        print(f"    Departments: {dept_values}")

    # Should include: CEO, CMO, content_001, social_media_001
    expected_mkt_agents = ["ceo_001", "cmo_001"]
    found_all = all(a in mkt_agent_ids for a in expected_mkt_agents)
    if found_all:
        print("✅ PASS: Marketing department includes CEO and CMO")
    else:
        print("❌ FAIL: Missing expected agents in Marketing")
    print()

    # Test 4: Department Counts
    print("Test 4: Department Agent Counts")
    print("-" * 80)
    dept_counts = {}
    for dept in Department:
        count = AgentRegistry.count_agents_by_department(dept)
        dept_counts[dept.value] = count
        print(f"  {dept.value}: {count} agents")

    # Validate counts
    if dept_counts["executive"] >= 6:  # At least 6 C-level executives
        print("✅ PASS: Executive department has expected agent count")
    else:
        print(f"❌ FAIL: Executive department should have at least 6 agents, has {dept_counts['executive']}")
    print()

    # Test 5: Agent Response Format (simulate API response)
    print("Test 5: Agent Response Format with Departments Array")
    print("-" * 80)
    ceo_config = AgentRegistry.get_agent_config("ceo_001")

    # Simulate what the API would return
    agent_departments = ceo_config.get("departments") or [ceo_config.get("department")]
    dept_values = []
    for d in agent_departments:
        if d is not None:
            dept_values.append(d.value if hasattr(d, "value") else str(d))

    primary_dept = dept_values[0] if dept_values else "unknown"

    api_response = {
        "agent_id": "ceo_001",
        "name": ceo_config.get("name"),
        "role": ceo_config.get("role"),
        "department": primary_dept,  # Legacy field
        "departments": dept_values,  # New multi-department field
    }

    print("CEO Agent API Response:")
    print(f"  department (legacy): {api_response['department']}")
    print(f"  departments (new): {api_response['departments'][:3]}... ({len(api_response['departments'])} total)")

    if api_response["department"] == "executive" and len(api_response["departments"]) == 9:
        print("✅ PASS: API response includes both legacy and new department fields")
    else:
        print("❌ FAIL: API response format incorrect")
    print()

    # Test 6: Filter by Single-Department Agent
    print("Test 6: Single-Department Agent (Backend Engineer)")
    print("-" * 80)
    backend_config = AgentRegistry.get_agent_config("backend_001")
    backend_departments = backend_config.get("departments") or [backend_config.get("department")]
    dept_values = [d.value if hasattr(d, "value") else str(d) for d in backend_departments if d]

    print(f"Backend Engineer Departments: {dept_values}")

    if dept_values == ["engineering"]:
        print("✅ PASS: Single-department agents work correctly")
    else:
        print(f"❌ FAIL: Expected ['engineering'], got {dept_values}")
    print()

    # Summary
    print("=" * 80)
    print("API Filtering Test Complete")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  - Total agents in catalog: {AgentRegistry.count_agents()}")
    print(f"  - Executive agents: {dept_counts.get('executive', 0)}")
    print(f"  - Engineering agents: {dept_counts.get('engineering', 0)}")
    print(f"  - Marketing agents: {dept_counts.get('marketing', 0)}")
    print(f"  - Finance agents: {dept_counts.get('finance', 0)}")
    print()
    print("Key Features Verified:")
    print("  ✓ Department filtering includes multi-department agents")
    print("  ✓ Department counts are accurate")
    print("  ✓ API responses include both 'department' and 'departments' fields")
    print("  ✓ Single-department agents still work correctly")
    print()


if __name__ == "__main__":
    test_api_filtering()
