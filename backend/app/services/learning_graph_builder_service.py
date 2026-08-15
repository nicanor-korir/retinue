"""
Learning Graph Builder Service

Builds and maintains a knowledge graph of cross-project relationships,
learning connections, and pattern usage across the organization.
"""

import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from collections import defaultdict
import json

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class GraphNode:
    """Represents a node in the learning graph"""

    def __init__(
        self,
        node_id: str,
        node_type: str,  # 'project', 'pattern', 'technology', 'domain'
        name: str,
        description: str,
        metadata: Dict[str, Any]
    ):
        self.node_id = node_id
        self.node_type = node_type
        self.name = name
        self.description = description
        self.metadata = metadata
        self.connections: List[Tuple[str, float]] = []  # (node_id, weight)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "name": self.name,
            "description": self.description,
            "metadata": self.metadata,
            "connection_count": len(self.connections)
        }


class GraphEdge:
    """Represents an edge between nodes in the learning graph"""

    def __init__(
        self,
        source_id: str,
        target_id: str,
        edge_type: str,  # 'uses', 'learns_from', 'similar_to', 'improves'
        weight: float,
        metadata: Dict[str, Any]
    ):
        self.source_id = source_id
        self.target_id = target_id
        self.edge_type = edge_type
        self.weight = weight
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type,
            "weight": self.weight,
            "metadata": self.metadata
        }


class LearningGraph:
    """Represents the learning graph structure"""

    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def add_node(self, node: GraphNode) -> None:
        """Add a node to the graph"""
        self.nodes[node.node_id] = node
        self.updated_at = datetime.utcnow()

    def add_edge(self, edge: GraphEdge) -> None:
        """Add an edge to the graph"""
        self.edges.append(edge)
        if edge.source_id in self.nodes:
            self.nodes[edge.source_id].connections.append((edge.target_id, edge.weight))
        self.updated_at = datetime.utcnow()

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by ID"""
        return self.nodes.get(node_id)

    def get_connected_nodes(self, node_id: str) -> List[GraphNode]:
        """Get all nodes connected to a specific node"""
        node = self.get_node(node_id)
        if not node:
            return []

        connected = []
        for connected_id, _ in node.connections:
            connected_node = self.get_node(connected_id)
            if connected_node:
                connected.append(connected_node)

        return connected

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class LearningGraphBuilderService:
    """Service for building and maintaining the learning graph"""

    def __init__(self):
        """Initialize the learning graph builder"""
        self.graph = LearningGraph()
        self.cache = {}
        self.cache_ttl = 600  # 10 minutes
        self.last_cache_update = {}

    async def build_graph(self, session: AsyncSession) -> LearningGraph:
        """
        Build the complete learning graph from database.

        Creates nodes for:
        - Projects
        - Patterns
        - Technologies
        - Domains

        Creates edges for:
        - Project uses Pattern
        - Pattern improves Success Rate
        - Project similar to Project
        - Technology used in Project
        """
        try:
            self.graph = LearningGraph()

            # Step 1: Create project nodes
            await self._add_project_nodes(session)

            # Step 2: Create pattern nodes
            await self._add_pattern_nodes(session)

            # Step 3: Create technology nodes
            await self._add_technology_nodes(session)

            # Step 4: Create domain nodes
            await self._add_domain_nodes(session)

            # Step 5: Create edges (relationships)
            await self._create_relationships(session)

            logger.info(f"Built learning graph with {len(self.graph.nodes)} nodes and {len(self.graph.edges)} edges")

            return self.graph

        except Exception as e:
            logger.error(f"Error building learning graph: {e}")
            return self.graph

    async def _add_project_nodes(self, session: AsyncSession) -> None:
        """Add project nodes to the graph"""
        try:
            from app.db.models import Project, ProjectStatus

            result = await session.execute(
                select(Project).where(
                    Project.created_at >= datetime.utcnow() - timedelta(days=180)
                )
            )

            projects = result.scalars().all()

            for project in projects:
                node = GraphNode(
                    node_id=f"proj_{project.project_id}",
                    node_type="project",
                    name=project.name,
                    description=project.description or "",
                    metadata={
                        "project_id": str(project.project_id),
                        "status": str(project.status) if hasattr(project, 'status') else "unknown",
                        "quality_score": getattr(project, 'quality_score', 0),
                        "created_at": project.created_at.isoformat() if hasattr(project, 'created_at') else ""
                    }
                )
                self.graph.add_node(node)

        except Exception as e:
            logger.error(f"Error adding project nodes: {e}")

    async def _add_pattern_nodes(self, session: AsyncSession) -> None:
        """Add pattern nodes to the graph"""
        try:
            from app.db.models import Task, TaskStatus

            result = await session.execute(
                select(Task).where(
                    and_(
                        Task.status == TaskStatus.COMPLETED,
                        Task.pattern_category.isnot(None),
                        Task.success_score >= 0.7
                    )
                )
            )

            tasks = result.scalars().all()

            # Group by pattern category
            patterns = defaultdict(list)
            for task in tasks:
                if task.pattern_category:
                    patterns[task.pattern_category].append(task)

            # Create pattern nodes
            for category, category_tasks in patterns.items():
                if len(category_tasks) >= 2:  # Only if multiple uses
                    avg_success = sum(t.success_score or 0 for t in category_tasks) / len(category_tasks)

                    node = GraphNode(
                        node_id=f"pattern_{category}",
                        node_type="pattern",
                        name=f"{category.replace('_', ' ').title()} Pattern",
                        description=f"Pattern used in {len(category_tasks)} tasks across {len(set(t.project_id for t in category_tasks))} projects",
                        metadata={
                            "category": category,
                            "usage_count": len(category_tasks),
                            "success_rate": avg_success,
                            "project_count": len(set(t.project_id for t in category_tasks))
                        }
                    )
                    self.graph.add_node(node)

        except Exception as e:
            logger.error(f"Error adding pattern nodes: {e}")

    async def _add_technology_nodes(self, session: AsyncSession) -> None:
        """Add technology nodes to the graph"""
        try:
            from app.db.models import Task, TaskStatus

            result = await session.execute(
                select(Task).where(
                    and_(
                        Task.status == TaskStatus.COMPLETED,
                        Task.technologies.isnot(None)
                    )
                )
            )

            tasks = result.scalars().all()

            # Collect all technologies
            all_techs = defaultdict(int)
            for task in tasks:
                if task.technologies:
                    for tech in task.technologies:
                        all_techs[tech] += 1

            # Create nodes for frequently used technologies
            for tech, count in all_techs.items():
                if count >= 2:  # Only if used in multiple tasks
                    node = GraphNode(
                        node_id=f"tech_{tech.lower().replace(' ', '_')}",
                        node_type="technology",
                        name=tech,
                        description=f"Technology used in {count} tasks",
                        metadata={
                            "usage_count": count,
                            "technology": tech
                        }
                    )
                    self.graph.add_node(node)

        except Exception as e:
            logger.error(f"Error adding technology nodes: {e}")

    async def _add_domain_nodes(self, session: AsyncSession) -> None:
        """Add domain nodes to the graph"""
        from app.services.domain_pattern_library_service import get_domain_pattern_library_service

        try:
            domain_service = get_domain_pattern_library_service()
            await domain_service.initialize_default_libraries(session)

            for domain_key, domain_info in domain_service.DOMAINS.items():
                node = GraphNode(
                    node_id=f"domain_{domain_key}",
                    node_type="domain",
                    name=domain_info["name"],
                    description=domain_info["description"],
                    metadata={
                        "domain_key": domain_key,
                        "keywords": domain_info["keywords"],
                        "technologies": domain_info["technologies"]
                    }
                )
                self.graph.add_node(node)

        except Exception as e:
            logger.error(f"Error adding domain nodes: {e}")

    async def _create_relationships(self, session: AsyncSession) -> None:
        """Create edges representing relationships between nodes"""
        try:
            from app.db.models import Task, Project, TaskStatus

            # Get all completed tasks for relationship building
            result = await session.execute(
                select(Task).where(Task.status == TaskStatus.COMPLETED)
            )

            tasks = result.scalars().all()

            # Create 'uses' edges (project uses pattern)
            for task in tasks:
                if task.pattern_category and task.project_id:
                    source_id = f"proj_{task.project_id}"
                    target_id = f"pattern_{task.pattern_category}"

                    if source_id in self.graph.nodes and target_id in self.graph.nodes:
                        weight = task.success_score or 0.5
                        edge = GraphEdge(
                            source_id=source_id,
                            target_id=target_id,
                            edge_type="uses",
                            weight=weight,
                            metadata={"task_count": 1}
                        )
                        self.graph.add_edge(edge)

            # Create 'uses_technology' edges
            for task in tasks:
                if task.technologies and task.project_id:
                    project_id = f"proj_{task.project_id}"

                    for tech in task.technologies:
                        tech_id = f"tech_{tech.lower().replace(' ', '_')}"

                        if project_id in self.graph.nodes and tech_id in self.graph.nodes:
                            edge = GraphEdge(
                                source_id=project_id,
                                target_id=tech_id,
                                edge_type="uses_technology",
                                weight=1.0,
                                metadata={}
                            )
                            self.graph.add_edge(edge)

            # Create 'similar_to' edges between projects
            # (simplified: projects with same technologies are similar)
            projects = {}
            for task in tasks:
                if task.project_id not in projects:
                    projects[task.project_id] = set()
                if task.technologies:
                    projects[task.project_id].update(task.technologies)

            project_ids = list(projects.keys())
            for i, proj1_id in enumerate(project_ids):
                for proj2_id in project_ids[i + 1:]:
                    techs1 = projects.get(proj1_id, set())
                    techs2 = projects.get(proj2_id, set())

                    if techs1 and techs2:
                        overlap = len(techs1 & techs2)
                        union = len(techs1 | techs2)
                        similarity = overlap / union if union > 0 else 0

                        if similarity >= 0.3:  # At least 30% similarity
                            source_id = f"proj_{proj1_id}"
                            target_id = f"proj_{proj2_id}"

                            if source_id in self.graph.nodes and target_id in self.graph.nodes:
                                edge = GraphEdge(
                                    source_id=source_id,
                                    target_id=target_id,
                                    edge_type="similar_to",
                                    weight=similarity,
                                    metadata={"overlap": overlap, "total": union}
                                )
                                self.graph.add_edge(edge)

            logger.info(f"Created {len(self.graph.edges)} relationships in learning graph")

        except Exception as e:
            logger.error(f"Error creating relationships: {e}")

    async def get_graph(self, session: AsyncSession) -> LearningGraph:
        """Get the current learning graph, rebuilding if necessary"""
        cache_key = "learning_graph"

        if cache_key in self.cache:
            if datetime.now() - self.last_cache_update.get(cache_key, datetime.min) < timedelta(seconds=self.cache_ttl):
                return self.cache[cache_key]

        graph = await self.build_graph(session)

        self.cache[cache_key] = graph
        self.last_cache_update[cache_key] = datetime.now()

        return graph

    async def find_learning_path(
        self,
        session: AsyncSession,
        start_node_id: str,
        target_node_id: str
    ) -> List[GraphNode]:
        """
        Find a learning path between two nodes.

        Uses breadth-first search to find the shortest path.
        """
        graph = await self.get_graph(session)

        if start_node_id not in graph.nodes or target_node_id not in graph.nodes:
            return []

        # BFS
        from collections import deque

        queue = deque([(start_node_id, [graph.nodes[start_node_id]])])
        visited = {start_node_id}

        while queue:
            current_id, path = queue.popleft()

            if current_id == target_node_id:
                return path

            current_node = graph.nodes.get(current_id)
            if not current_node:
                continue

            for next_id, _ in current_node.connections:
                if next_id not in visited:
                    visited.add(next_id)
                    next_node = graph.nodes.get(next_id)
                    if next_node:
                        queue.append((next_id, path + [next_node]))

        return []

    async def get_node_statistics(
        self,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Get statistics about the learning graph"""
        graph = await self.get_graph(session)

        if not graph.nodes:
            return {
                "node_count": 0,
                "edge_count": 0,
                "node_types": {},
                "edge_types": {}
            }

        # Count by type
        node_types = defaultdict(int)
        for node in graph.nodes.values():
            node_types[node.node_type] += 1

        edge_types = defaultdict(int)
        for edge in graph.edges:
            edge_types[edge.edge_type] += 1

        return {
            "node_count": len(graph.nodes),
            "edge_count": len(graph.edges),
            "node_types": dict(node_types),
            "edge_types": dict(edge_types),
            "created_at": graph.created_at.isoformat(),
            "updated_at": graph.updated_at.isoformat()
        }


# Singleton instance
_learning_graph_builder_service: Optional[LearningGraphBuilderService] = None


def get_learning_graph_builder_service() -> LearningGraphBuilderService:
    """Get or create the learning graph builder service singleton"""
    global _learning_graph_builder_service
    if _learning_graph_builder_service is None:
        _learning_graph_builder_service = LearningGraphBuilderService()
    return _learning_graph_builder_service
