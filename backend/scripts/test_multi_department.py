#!/usr/bin/env python3
"""Test script for multi-department agent support.

This script verifies that the multi-department functionality works correctly:
1. AgentRegistry properly handles multi-department agents
2. get_agents_by_department returns agents from all their departments
3. Helper methods (get_primary_department, get_all_departments) work correctly
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


def test_multi_department_agents():
    """Test multi-department agent configuration."""
    print("=" * 80)
    print("Testing Multi-Department Agent Support")
    print("=" * 80)
    print()

    # Test 1: Verify CEO has all departments
    print("Test 1: CEO Agent - Should be in ALL departments")
    print("-" * 80)
    ceo_config = AgentRegistry.get_agent_config("ceo_001")
    ceo_departments = ceo_config.get("departments", [])
    print(f"CEO Departments ({len(ceo_departments)}): {[d.value for d in ceo_departments]}")

    expected_dept_count = len(Department)
    if len(ceo_departments) == expected_dept_count:
        print("✅ PASS: CEO has access to all departments")
    else:
        print(f"❌ FAIL: CEO should have {expected_dept_count} departments, has {len(ceo_departments)}")
    print()

    # Test 2: Verify CTO is in multiple departments
    print("Test 2: CTO Agent - Should be in Engineering, Executive, and Research")
    print("-" * 80)
    cto_config = AgentRegistry.get_agent_config("cto_001")
    cto_departments = [d.value for d in cto_config.get("departments", [])]
    print(f"CTO Departments: {cto_departments}")

    expected_cto_depts = ["engineering", "executive", "research"]
    if cto_departments == expected_cto_depts:
        print("✅ PASS: CTO has correct departments")
    else:
        print(f"❌ FAIL: CTO should have {expected_cto_depts}")
    print()

    # Test 3: Verify CFO is in multiple departments
    print("Test 3: CFO Agent - Should be in Finance, Executive, and Operations")
    print("-" * 80)
    cfo_config = AgentRegistry.get_agent_config("cfo_001")
    cfo_departments = [d.value for d in cfo_config.get("departments", [])]
    print(f"CFO Departments: {cfo_departments}")

    expected_cfo_depts = ["finance", "executive", "operations"]
    if cfo_departments == expected_cfo_depts:
        print("✅ PASS: CFO has correct departments")
    else:
        print(f"❌ FAIL: CFO should have {expected_cfo_depts}")
    print()

    # Test 4: Test get_agents_by_department - Executive should include CEO, CTO, CFO, etc.
    print("Test 4: get_agents_by_department('executive') - Should include all C-level")
    print("-" * 80)
    exec_agents = AgentRegistry.get_agents_by_department(Department.EXECUTIVE)
    exec_agent_ids = [a["agent_id"] for a in exec_agents]
    print(f"Executive Department Agents ({len(exec_agents)}):")
    for agent in exec_agents:
        print(f"  - {agent['agent_id']}: {agent['name']} ({agent['role']})")

    expected_exec_agents = ["ceo_001", "cto_001", "cfo_001", "cmo_001", "chro_001", "coo_001"]
    found_all = all(agent_id in exec_agent_ids for agent_id in expected_exec_agents)
    if found_all:
        print(f"✅ PASS: All expected C-level agents found in Executive department")
    else:
        missing = [a for a in expected_exec_agents if a not in exec_agent_ids]
        print(f"❌ FAIL: Missing agents: {missing}")
    print()

    # Test 5: Test get_agents_by_department - Engineering should include CTO but also CEO
    print("Test 5: get_agents_by_department('engineering') - Should include CTO and CEO")
    print("-" * 80)
    eng_agents = AgentRegistry.get_agents_by_department(Department.ENGINEERING)
    eng_agent_ids = [a["agent_id"] for a in eng_agents]
    print(f"Engineering Department Agents ({len(eng_agents)}):")
    for agent in eng_agents:
        print(f"  - {agent['agent_id']}: {agent['name']} ({agent['role']})")

    if "cto_001" in eng_agent_ids and "ceo_001" in eng_agent_ids:
        print("✅ PASS: CTO and CEO both found in Engineering department")
    else:
        print(f"❌ FAIL: CTO or CEO not found in Engineering")
    print()

    # Test 6: Test helper methods
    print("Test 6: Helper Methods - get_primary_department and get_all_departments")
    print("-" * 80)

    ceo_primary = AgentRegistry.get_primary_department("ceo_001")
    ceo_all = AgentRegistry.get_all_departments("ceo_001")
    print(f"CEO Primary Department: {ceo_primary}")
    print(f"CEO All Departments ({len(ceo_all)}): {ceo_all[:3]}... (showing first 3)")

    if ceo_primary == "executive" and len(ceo_all) == expected_dept_count:
        print("✅ PASS: Helper methods work correctly")
    else:
        print(f"❌ FAIL: Helper methods returned unexpected values")
    print()

    # Test 7: Single department agents still work
    print("Test 7: Single Department Agents - Backend Engineer should only be in Engineering")
    print("-" * 80)
    backend_config = AgentRegistry.get_agent_config("backend_001")
    backend_departments = [d.value for d in backend_config.get("departments", [])]
    print(f"Backend Engineer Departments: {backend_departments}")

    if backend_departments == ["engineering"]:
        print("✅ PASS: Single department agents work correctly")
    else:
        print(f"❌ FAIL: Backend Engineer should only be in ['engineering']")
    print()

    # Summary
    print("=" * 80)
    print("Multi-Department Agent Testing Complete")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  - Total agents in catalog: {AgentRegistry.count_agents()}")
    print(f"  - Executive department agents: {AgentRegistry.count_agents_by_department(Department.EXECUTIVE)}")
    print(f"  - Engineering department agents: {AgentRegistry.count_agents_by_department(Department.ENGINEERING)}")
    print(f"  - Finance department agents: {AgentRegistry.count_agents_by_department(Department.FINANCE)}")
    print(f"  - Marketing department agents: {AgentRegistry.count_agents_by_department(Department.MARKETING)}")
    print()


if __name__ == "__main__":
    test_multi_department_agents()
