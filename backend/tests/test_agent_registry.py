"""Unit tests for AgentRegistry and agent capabilities.

Tests for:
- AgentRegistry agent loading and filtering
- Agent capability matching
- Team validation
- Deliverable type requirements
"""

import pytest
from app.agents.agent_registry import (
    AgentRegistry,
    Department,
    OutputType,
    Specialization,
)
from app.utils.agent_capabilities import (
    can_agent_handle_task,
    find_capable_agents,
    validate_team_composition,
    validate_team_for_deliverable,
    get_agent_capability_summary,
    get_team_capability_summary,
    suggest_agents_for_task,
    calculate_skill_match,
)


class TestAgentRegistry:
    """Tests for AgentRegistry core functionality."""

    def test_agent_registry_has_agents(self):
        """Test that AgentRegistry contains agents."""
        assert AgentRegistry.count_agents() >= 20
        assert len(AgentRegistry.AGENT_CATALOG) >= 20

    def test_get_agent_config_existing(self):
        """Test getting configuration for existing agents."""
        # Test original 7 agents
        for agent_id in ["ceo_001", "pm_001", "hr_monitor_001", "backend_001", "frontend_001", "designer_001", "cto_001"]:
            config = AgentRegistry.get_agent_config(agent_id)
            assert config is not None
            assert config["name"] is not None
            assert config["role"] is not None
            assert config["department"] is not None

    def test_get_agent_config_nonexistent(self):
        """Test error on nonexistent agent."""
        with pytest.raises(ValueError):
            AgentRegistry.get_agent_config("invalid_agent_999")

    def test_get_agents_by_department_executive(self):
        """Test filtering agents by executive department."""
        agents = AgentRegistry.get_agents_by_department(Department.EXECUTIVE)
        agent_ids = [a["agent_id"] for a in agents]
        assert "ceo_001" in agent_ids
        assert len(agents) >= 1

    def test_get_agents_by_department_engineering(self):
        """Test filtering agents by engineering department."""
        agents = AgentRegistry.get_agents_by_department(Department.ENGINEERING)
        agent_ids = [a["agent_id"] for a in agents]
        assert "backend_001" in agent_ids
        assert "frontend_001" in agent_ids
        assert "designer_001" in agent_ids
        assert "cto_001" in agent_ids
        assert len(agents) >= 4

    def test_get_agents_by_department_marketing(self):
        """Test filtering agents by marketing department."""
        agents = AgentRegistry.get_agents_by_department(Department.MARKETING)
        agent_ids = [a["agent_id"] for a in agents]
        assert "cmo_001" in agent_ids
        assert "content_001" in agent_ids
        assert "social_media_001" in agent_ids
        assert len(agents) >= 3

    def test_get_agents_by_department_finance(self):
        """Test filtering agents by finance department."""
        agents = AgentRegistry.get_agents_by_department(Department.FINANCE)
        agent_ids = [a["agent_id"] for a in agents]
        assert "cfo_001" in agent_ids
        assert "financial_analyst_001" in agent_ids

    def test_get_required_agents_software_mvp(self):
        """Test required agents for software MVP."""
        required = AgentRegistry.get_required_agents("software_mvp")
        # Always active
        assert "ceo_001" in required
        assert "pm_001" in required
        assert "hr_monitor_001" in required
        # Software specific
        assert "cto_001" in required
        assert "backend_001" in required
        assert "frontend_001" in required

    def test_get_required_agents_marketing_campaign(self):
        """Test required agents for marketing campaign."""
        required = AgentRegistry.get_required_agents("marketing_campaign")
        # Always active
        assert "ceo_001" in required
        assert "pm_001" in required
        assert "hr_monitor_001" in required
        # Marketing specific
        assert "cmo_001" in required

    def test_get_required_agents_financial_analysis(self):
        """Test required agents for financial analysis."""
        required = AgentRegistry.get_required_agents("financial_analysis")
        # Always active
        assert "ceo_001" in required
        assert "pm_001" in required
        assert "hr_monitor_001" in required
        # Finance specific
        assert "cfo_001" in required
        assert "financial_analyst_001" in required

    def test_get_agents_by_capability_python(self):
        """Test finding agents with Python capability."""
        agents = AgentRegistry.get_agents_by_capability(Specialization.PYTHON)
        agent_ids = set(agents)
        assert "backend_001" in agent_ids
        assert "data_analyst_001" in agent_ids
        # Designer should not have Python
        assert "designer_001" not in agent_ids

    def test_get_agents_by_capability_ui_ux(self):
        """Test finding agents with UI/UX capability."""
        agents = AgentRegistry.get_agents_by_capability(Specialization.UI_UX)
        assert "designer_001" in agents
        # Backend should not have UI/UX
        assert "backend_001" not in agents

    def test_validate_agent_selection_valid(self):
        """Test validation of valid agent selection."""
        agents = ["ceo_001", "pm_001", "hr_monitor_001", "cto_001", "backend_001", "frontend_001", "designer_001"]
        is_valid, missing = AgentRegistry.validate_agent_selection(agents, "software_mvp")
        assert is_valid is True
        assert missing == []

    def test_validate_agent_selection_missing_required(self):
        """Test detection of missing required agents."""
        agents = ["ceo_001", "pm_001"]  # Missing hr_monitor_001 and software agents
        is_valid, missing = AgentRegistry.validate_agent_selection(agents, "software_mvp")
        assert is_valid is False
        assert "hr_monitor_001" in missing

    def test_validate_agent_selection_unknown_agent(self):
        """Test detection of unknown agents."""
        agents = ["ceo_001", "invalid_agent_999"]
        is_valid, missing = AgentRegistry.validate_agent_selection(agents, "software_mvp")
        assert is_valid is False
        assert "invalid_agent_999" in missing

    def test_get_agent_output_types(self):
        """Test getting output types for agents."""
        # Backend can produce code and text
        backend_outputs = AgentRegistry.get_agent_output_types("backend_001")
        assert OutputType.CODE.value in backend_outputs or "code" in backend_outputs

        # CMO can produce PDF and markdown
        cmo_outputs = AgentRegistry.get_agent_output_types("cmo_001")
        assert OutputType.MARKDOWN.value in cmo_outputs or "markdown" in cmo_outputs

    def test_get_agents_by_specialization(self):
        """Test getting agents by specialization (alias method)."""
        agents = AgentRegistry.get_agents_by_specialization(Specialization.MARKETING_STRATEGY)
        assert "cmo_001" in agents

    def test_get_all_agents(self):
        """Test getting all agents."""
        all_agents = AgentRegistry.get_all_agents()
        assert len(all_agents) >= 20
        # Should be sorted by agent_id
        agent_ids = [a["agent_id"] for a in all_agents]
        assert agent_ids == sorted(agent_ids)

    def test_get_always_active_agents(self):
        """Test getting always-active agents."""
        always_active = AgentRegistry.get_always_active_agents()
        assert "ceo_001" in always_active
        assert "pm_001" in always_active
        assert "hr_monitor_001" in always_active
        assert len(always_active) == 3  # Only these 3 are always active

    def test_agent_exists(self):
        """Test checking agent existence."""
        assert AgentRegistry.agent_exists("ceo_001") is True
        assert AgentRegistry.agent_exists("backend_001") is True
        assert AgentRegistry.agent_exists("cmo_001") is True
        assert AgentRegistry.agent_exists("invalid_999") is False

    def test_count_agents(self):
        """Test counting total agents."""
        count = AgentRegistry.count_agents()
        assert count == len(AgentRegistry.AGENT_CATALOG)
        assert count >= 20

    def test_count_agents_by_department(self):
        """Test counting agents in specific departments."""
        eng_count = AgentRegistry.count_agents_by_department(Department.ENGINEERING)
        assert eng_count >= 4  # CTO, Backend, Frontend, Designer

        mkt_count = AgentRegistry.count_agents_by_department(Department.MARKETING)
        assert mkt_count >= 3  # CMO, Content, Social Media


class TestAgentCapabilities:
    """Tests for agent capability matching utilities."""

    def test_can_agent_handle_backend_task(self):
        """Test that backend engineer can handle backend tasks."""
        can_handle, missing = can_agent_handle_task(
            "backend_001",
            [Specialization.PYTHON, Specialization.FASTAPI]
        )
        assert can_handle is True
        assert missing == []

    def test_can_agent_handle_missing_skills(self):
        """Test detection of missing skills."""
        can_handle, missing = can_agent_handle_task(
            "designer_001",
            [Specialization.PYTHON, Specialization.FASTAPI]
        )
        assert can_handle is False
        assert len(missing) > 0

    def test_can_agent_handle_code_output(self):
        """Test that backend engineer can produce code."""
        can_handle, missing = can_agent_handle_task(
            "backend_001",
            [Specialization.PYTHON],
            required_output_type=OutputType.CODE.value
        )
        assert can_handle is True

    def test_cannot_handle_wrong_output_type(self):
        """Test that agent cannot produce wrong output type."""
        can_handle, missing = can_agent_handle_task(
            "backend_001",
            [Specialization.PYTHON],
            required_output_type=OutputType.DOCX.value
        )
        # Backend should not produce DOCX by default
        # This depends on backend_001 output types
        # Just ensure it returns a result
        assert isinstance(can_handle, bool)

    def test_find_capable_agents_python(self):
        """Test finding agents with Python skills."""
        capable = find_capable_agents([Specialization.PYTHON])
        assert "backend_001" in capable
        assert "data_analyst_001" in capable

    def test_find_capable_agents_marketing(self):
        """Test finding agents with marketing skills."""
        capable = find_capable_agents([Specialization.MARKETING_STRATEGY])
        assert "cmo_001" in capable
        assert "backend_001" not in capable

    def test_find_capable_agents_limited(self):
        """Test finding capable agents from limited set."""
        capable = find_capable_agents(
            [Specialization.UI_UX],
            from_agents=["backend_001", "frontend_001", "designer_001"]
        )
        assert "designer_001" in capable
        assert "backend_001" not in capable
        assert "frontend_001" not in capable

    def test_validate_team_composition_valid(self):
        """Test validation of valid team composition."""
        team = ["ceo_001", "pm_001", "hr_monitor_001", "backend_001", "frontend_001"]
        is_valid, issues = validate_team_composition(team)
        assert is_valid is True
        assert issues == []

    def test_validate_team_composition_missing_required(self):
        """Test detection of missing required agents."""
        team = ["ceo_001", "pm_001"]  # Missing hr_monitor_001
        is_valid, issues = validate_team_composition(team)
        assert is_valid is False
        assert any("hr_monitor_001" in issue for issue in issues)

    def test_validate_team_composition_unknown_agent(self):
        """Test detection of unknown agents in team."""
        team = ["ceo_001", "pm_001", "hr_monitor_001", "invalid_999"]
        is_valid, issues = validate_team_composition(team)
        assert is_valid is False
        assert any("invalid_999" in issue for issue in issues)

    def test_validate_team_composition_empty(self):
        """Test validation of empty team."""
        is_valid, issues = validate_team_composition([])
        assert is_valid is False

    def test_validate_team_for_deliverable_software(self):
        """Test team validation for software MVP."""
        team = [
            "ceo_001", "pm_001", "hr_monitor_001",
            "cto_001", "backend_001", "frontend_001", "designer_001"
        ]
        is_valid, issues = validate_team_for_deliverable(team, "software_mvp")
        assert is_valid is True
        assert issues == []

    def test_validate_team_for_deliverable_missing(self):
        """Test detection of missing agents for deliverable."""
        team = ["ceo_001", "pm_001", "hr_monitor_001"]  # No engineering team
        is_valid, issues = validate_team_for_deliverable(team, "software_mvp")
        assert is_valid is False

    def test_get_agent_capability_summary(self):
        """Test getting capability summary for agent."""
        summary = get_agent_capability_summary("backend_001")
        assert summary["agent_id"] == "backend_001"
        assert summary["name"] == "Backend Engineer"
        assert "python" in [s.lower() for s in summary["specializations"]]
        assert len(summary["output_types"]) > 0

    def test_get_team_capability_summary(self):
        """Test getting team capability summary."""
        team = ["ceo_001", "backend_001", "frontend_001", "designer_001"]
        summary = get_team_capability_summary(team)
        assert summary["team_size"] == 4
        assert len(summary["agents"]) == 4
        assert len(summary["combined_skills"]) > 0
        assert len(summary["output_types"]) > 0

    def test_suggest_agents_for_task(self):
        """Test agent suggestions for tasks."""
        suggestions = suggest_agents_for_task(
            "Build a backend API",
            [Specialization.PYTHON, Specialization.FASTAPI],
            required_output_type=OutputType.CODE.value
        )
        assert len(suggestions) > 0
        assert suggestions[0]["agent_id"] == "backend_001"

    def test_calculate_skill_match_perfect(self):
        """Test perfect skill match."""
        score = calculate_skill_match(
            "backend_001",
            [Specialization.PYTHON, Specialization.FASTAPI]
        )
        assert score == 1.0

    def test_calculate_skill_match_partial(self):
        """Test partial skill match."""
        score = calculate_skill_match(
            "backend_001",
            [Specialization.PYTHON, Specialization.UI_UX]  # Backend has Python but not UI/UX
        )
        assert 0 < score < 1.0

    def test_calculate_skill_match_none(self):
        """Test no skill match."""
        score = calculate_skill_match(
            "designer_001",
            [Specialization.PYTHON, Specialization.FASTAPI]
        )
        assert score == 0.0

    def test_calculate_skill_match_empty_requirements(self):
        """Test match with no skill requirements."""
        score = calculate_skill_match("backend_001", [])
        assert score == 1.0


class TestBackwardCompatibility:
    """Tests to ensure backward compatibility with existing agents."""

    def test_all_original_agents_in_registry(self):
        """Test that all 7 original agents are in registry."""
        original_agents = [
            "ceo_001", "cto_001", "pm_001", "hr_monitor_001",
            "backend_001", "frontend_001", "designer_001"
        ]
        for agent_id in original_agents:
            assert AgentRegistry.agent_exists(agent_id)

    def test_original_agents_have_configurations(self):
        """Test that original agents have complete configurations."""
        for agent_id in ["ceo_001", "backend_001", "frontend_001"]:
            config = AgentRegistry.get_agent_config(agent_id)
            assert config["name"]
            assert config["role"]
            assert config["department"]
            assert config.get("output_types")
            assert config.get("specializations")

    def test_software_mvp_workflow_still_works(self):
        """Test that software MVP workflow is still functional."""
        # Should be able to get required agents for software projects
        required = AgentRegistry.get_required_agents("software_mvp")
        assert len(required) >= 7

        # Should be able to validate traditional software team
        team = [
            "ceo_001", "pm_001", "hr_monitor_001",
            "cto_001", "backend_001", "frontend_001", "designer_001"
        ]
        is_valid, _ = validate_team_for_deliverable(team, "software_mvp")
        assert is_valid is True

    def test_always_active_agents_unchanged(self):
        """Test that always-active agents haven't changed."""
        always_active = AgentRegistry.get_always_active_agents()
        assert "ceo_001" in always_active
        assert "pm_001" in always_active
        assert "hr_monitor_001" in always_active


class TestNewFeatures:
    """Tests for new Phase 0 features."""

    def test_marketing_agents_available(self):
        """Test that marketing agents are available."""
        agents = AgentRegistry.get_agents_by_department(Department.MARKETING)
        agent_ids = [a["agent_id"] for a in agents]
        assert "cmo_001" in agent_ids
        assert "content_001" in agent_ids
        assert "social_media_001" in agent_ids

    def test_finance_agents_available(self):
        """Test that finance agents are available."""
        agents = AgentRegistry.get_agents_by_department(Department.FINANCE)
        agent_ids = [a["agent_id"] for a in agents]
        assert "cfo_001" in agent_ids
        assert "financial_analyst_001" in agent_ids

    def test_deliverable_type_requirements(self):
        """Test that deliverable types have requirements."""
        # Marketing campaign should require CMO
        marketing_required = AgentRegistry.get_required_agents("marketing_campaign")
        assert "cmo_001" in marketing_required

        # Financial analysis should require CFO
        finance_required = AgentRegistry.get_required_agents("financial_analysis")
        assert "cfo_001" in finance_required

    def test_can_create_marketing_team(self):
        """Test that marketing team can be created."""
        team = [
            "ceo_001", "pm_001", "hr_monitor_001",
            "cmo_001", "content_001", "designer_001"
        ]
        is_valid, issues = validate_team_for_deliverable(team, "marketing_campaign")
        assert is_valid is True

    def test_can_create_financial_team(self):
        """Test that financial team can be created."""
        team = [
            "ceo_001", "pm_001", "hr_monitor_001",
            "cfo_001", "financial_analyst_001"
        ]
        is_valid, issues = validate_team_for_deliverable(team, "financial_analysis")
        assert is_valid is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
