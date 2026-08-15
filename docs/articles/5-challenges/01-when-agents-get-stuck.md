# When AI Agents Get Stuck: Debugging Autonomous Systems

*The unglamorous reality of debugging AI that runs without you watching.*

---

## The 3 AM Mystery

It started with a Slack notification: "Project X hasn't progressed in 4 hours."

I checked the dashboard. All agents showed "healthy." No error logs. No failed tasks. Just... nothing happening.

The Backend Engineer had been "IN_PROGRESS" on a task for 4 hours. The CTO was waiting for output to review. The PM was waiting for the task to complete. Everyone waiting. No one working.

Welcome to debugging autonomous systems.

---

## The Failure Taxonomy

After months of running Retinue, I've catalogued the ways agents get stuck:

### 1. The Silent Loop

**What happens:** Agent keeps trying the same approach, failing, and retrying. No errors surfaced. No progress made.

**Example:**
```
Backend Engineer thinking...
Backend Engineer: Generating auth code
[LLM returns same code that already exists]
Backend Engineer: Task output ready
[CTO reviews, finds it doesn't build on previous iteration]
Backend Engineer: Revising...
Backend Engineer: Generating auth code
[Same code again]
```

**The fix:**
```python
class LoopDetector:
    async def check_output_novelty(
        self,
        new_output: str,
        previous_outputs: List[str]
    ) -> bool:
        for prev in previous_outputs[-3:]:  # Check last 3
            similarity = self.compute_similarity(new_output, prev)
            if similarity > 0.9:  # 90% similar
                return False  # Not novel enough
        return True

    async def on_output_ready(self, task: Task, output: str):
        history = await self.get_output_history(task.id)

        if not await self.check_output_novelty(output, history):
            # Break the loop
            await self.escalate(
                title=f"Loop detected in task {task.id}",
                message="Agent producing similar outputs repeatedly"
            )
            await self.request_different_approach(task)
```

### 2. The Dependency Deadlock

**What happens:** Task A waits for Task B. Task B waits for Task A. Nothing can proceed.

**Example:**
```
Task: "Implement API endpoint"
  depends_on: ["Database schema"]

Task: "Create database schema"
  depends_on: ["API endpoint spec"]  # Circular!
```

**The fix:**
```python
class DependencyResolver:
    async def validate_dependencies(self, tasks: List[Task]) -> List[str]:
        graph = self.build_dependency_graph(tasks)
        cycles = self.find_cycles(graph)

        if cycles:
            return [
                f"Circular dependency: {' -> '.join(cycle)}"
                for cycle in cycles
            ]
        return []

    async def on_task_created(self, task: Task):
        # Check for cycles before accepting
        project_tasks = await self.get_project_tasks(task.project_id)
        project_tasks.append(task)

        cycles = await self.validate_dependencies(project_tasks)
        if cycles:
            await self.reject_task(task, reason=cycles[0])
            await self.escalate_to_pm(
                project_id=task.project_id,
                issue="Circular dependencies detected"
            )
```

### 3. The Resource Starvation

**What happens:** Agent starts work, makes LLM call, connection drops, no result, no error, agent waits forever.

**Example:**
```
10:00:00 - Backend Engineer: Starting LLM call
10:00:00 - Anthropic API: Connection opened
10:00:15 - [Network blip, connection silently dropped]
10:00:15 - Backend Engineer: [Still waiting for response...]
12:00:00 - [Still waiting...]
```

**The fix:**
```python
class ResilientLLMClient:
    async def call_with_timeout(
        self,
        prompt: str,
        timeout_seconds: int = 120
    ) -> str:
        try:
            return await asyncio.wait_for(
                self.llm.generate(prompt),
                timeout=timeout_seconds
            )
        except asyncio.TimeoutError:
            # Log and retry
            logger.warning("LLM call timed out, retrying")
            return await self.call_with_timeout(prompt, timeout_seconds)
        except Exception as e:
            # Surface the error
            raise LLMCallFailed(f"LLM call failed: {e}")

    async def call_with_circuit_breaker(self, prompt: str) -> str:
        if self.circuit_open:
            # Fast fail if LLM is having issues
            raise CircuitBreakerOpen("LLM service degraded")

        try:
            result = await self.call_with_timeout(prompt)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            if self.failure_rate > 0.5:
                self.open_circuit()
            raise
```

### 4. The Context Confusion

**What happens:** Agent loses track of what it's doing mid-task. Output is incoherent or unrelated to the task.

**Example:**
```
Task: "Implement user profile page"

Backend Engineer output:
"Here's the implementation for the shopping cart..."

[Wrong context loaded]
```

**The fix:**
```python
class ContextValidator:
    async def validate_output_relevance(
        self,
        task: Task,
        output: str
    ) -> float:
        # Use LLM to check relevance
        check_prompt = f"""
        Task: {task.title}
        Description: {task.description}

        Output:
        {output[:2000]}

        Score the relevance of this output to the task (0-1):
        """

        score = await self.llm.generate(check_prompt)
        return float(score)

    async def on_output_ready(self, task: Task, output: str):
        relevance = await self.validate_output_relevance(task, output)

        if relevance < 0.7:
            logger.warning(f"Low relevance output for task {task.id}")
            await self.request_retry(
                task,
                reason="Output doesn't appear relevant to task"
            )
```

### 5. The Eternal Review

**What happens:** Reviewer (CTO) keeps requesting minor changes. Task never completes. Engineer keeps revising.

**Example:**
```
CTO: "Add error handling"
Engineer: [Adds error handling]
CTO: "Also add logging"
Engineer: [Adds logging]
CTO: "Also add tests"
Engineer: [Adds tests]
CTO: "The tests could be more comprehensive"
[Continues forever...]
```

**The fix:**
```python
class ReviewLimiter:
    MAX_REVISIONS = 3

    async def on_revision_requested(self, task: Task):
        task.revision_count += 1

        if task.revision_count >= self.MAX_REVISIONS:
            # Force a decision
            await self.escalate(
                title=f"Task {task.id} stuck in review",
                message=f"Revision count: {task.revision_count}",
                to_agent="PM"
            )

            # PM must either approve as-is or redefine the task
            decision = await self.request_pm_decision(task)

            if decision == "approve_as_is":
                await self.force_approve(task)
            elif decision == "redefine":
                await self.redefine_task(task)
            else:
                await self.cancel_task(task)
```

---

## The Debugging Toolkit

### 1. Activity Tracing

Every agent action is logged with full context:

```python
class ActivityTracer:
    async def trace_action(
        self,
        agent: Agent,
        action: str,
        context: dict
    ):
        await self.log({
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent.id,
            "agent_name": agent.name,
            "action": action,
            "context": context,
            "stack_trace": self.get_current_stack(),
            "task_id": self.get_current_task_id(),
            "project_id": self.get_current_project_id()
        })

# Usage
await tracer.trace_action(
    backend_engineer,
    "generating_code",
    {
        "task_title": task.title,
        "prompt_length": len(prompt),
        "context_tokens": context_tokens
    }
)
```

### 2. State Snapshots

Periodic dumps of complete system state:

```python
class StateSnapshotter:
    async def snapshot(self) -> SystemSnapshot:
        return SystemSnapshot(
            timestamp=datetime.now(),
            agents=[
                await self.snapshot_agent(a)
                for a in await self.get_all_agents()
            ],
            projects=[
                await self.snapshot_project(p)
                for p in await self.get_active_projects()
            ],
            pending_events=await self.get_pending_events(),
            stuck_tasks=await self.find_stuck_tasks()
        )

    async def snapshot_agent(self, agent: Agent) -> AgentSnapshot:
        return AgentSnapshot(
            agent_id=agent.id,
            status=agent.status,
            current_task=agent.current_task_id,
            last_action=agent.last_action,
            last_action_time=agent.last_action_time,
            consecutive_failures=agent.consecutive_failures
        )
```

### 3. Replay Debugging

Replay events to reproduce issues:

```python
class EventReplayer:
    async def replay_from_snapshot(
        self,
        snapshot: SystemSnapshot,
        until: datetime
    ):
        # Restore state
        await self.restore_state(snapshot)

        # Replay events in order
        events = await self.get_events_in_range(
            start=snapshot.timestamp,
            end=until
        )

        for event in events:
            await self.replay_event(event)
            await self.check_for_issue()  # Breakpoint

    async def replay_event(self, event: Event):
        logger.info(f"Replaying: {event.type} at {event.timestamp}")
        await self.event_bus.publish(event)
        await asyncio.sleep(0.1)  # Slow motion
```

---

## Prevention Strategies

### 1. Health Checks

Regular liveness and progress checks:

```python
class HealthChecker:
    async def check_agent_health(self, agent: Agent) -> HealthStatus:
        checks = [
            ("responsive", await self.is_responsive(agent)),
            ("making_progress", await self.is_making_progress(agent)),
            ("within_limits", await self.is_within_limits(agent)),
            ("no_errors", await self.has_no_recent_errors(agent))
        ]

        failed = [name for name, passed in checks if not passed]

        if len(failed) == 0:
            return HealthStatus.HEALTHY
        elif len(failed) == 1:
            return HealthStatus.WARNING
        else:
            return HealthStatus.CRITICAL

    async def is_making_progress(self, agent: Agent) -> bool:
        # Must have activity in last 30 minutes if has assigned task
        if not agent.current_task_id:
            return True

        last_activity = await self.get_last_activity(agent.id)
        return (datetime.now() - last_activity) < timedelta(minutes=30)
```

### 2. Watchdogs

Independent monitors that trigger when things go wrong:

```python
class TaskWatchdog:
    async def monitor_loop(self):
        while True:
            await asyncio.sleep(60)  # Check every minute

            for task in await self.get_active_tasks():
                if await self.is_stuck(task):
                    await self.trigger_intervention(task)

    async def is_stuck(self, task: Task) -> bool:
        time_in_status = datetime.now() - task.status_updated_at

        thresholds = {
            "IN_PROGRESS": timedelta(hours=2),
            "REVIEW": timedelta(hours=4),
            "BLOCKED": timedelta(hours=1),
        }

        threshold = thresholds.get(task.status)
        return threshold and time_in_status > threshold
```

### 3. Automatic Recovery

Self-healing when issues are detected:

```python
class AutoRecovery:
    async def recover_stuck_task(self, task: Task):
        # Try progressively aggressive recovery

        # Level 1: Retry with same agent
        if task.retry_count < 2:
            await self.retry_task(task)
            return

        # Level 2: Reset and retry
        if task.retry_count < 4:
            await self.reset_task_state(task)
            await self.retry_task(task)
            return

        # Level 3: Reassign to different agent
        if await self.can_reassign(task):
            await self.reassign_task(task)
            return

        # Level 4: Escalate to human
        await self.escalate_to_human(task)
```

---

## The Honest Reality

Despite all these safeguards, agents still get stuck. Here's my actual experience:

**Per 100 tasks:**
- 85-90 complete without issues
- 5-10 hit a recoverable problem
- 2-5 require human intervention

**Most common root causes:**
1. Ambiguous task specifications (40%)
2. LLM generating wrong approach (25%)
3. Infrastructure/network issues (20%)
4. Actual bugs in Retinue code (15%)

**Time to detection:**
- With HR monitoring: 30-60 minutes
- Without monitoring: Hours to never

---

## The Takeaway

Autonomous systems fail in autonomous ways. You can't watch every action, so you need:

1. **Detection**: Monitoring that catches stuck states
2. **Diagnosis**: Logging that explains what happened
3. **Recovery**: Automatic remediation when possible
4. **Escalation**: Human handoff when not

The goal isn't zero failures. It's fast detection and graceful recovery.

---

**Next**: [The Cost of Intelligence: LLM API Economics →](./02-cost-of-intelligence.md)

---

*Nicanor Korir has spent too many hours debugging silent failures. These patterns are the result.*
