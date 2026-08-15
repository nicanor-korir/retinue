"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { useCreateProject, useAvailableAgents } from "@/hooks/useApi";
import {
  ArrowLeft,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Zap,
  Users,
  Brain,
  Code,
  Palette,
  Clock,
  Target,
  BarChart3,
  TrendingUp,
  FileText,
  Briefcase,
  Shield,
  Lightbulb,
} from "lucide-react";
import { Priority } from "@/types/api";
import Link from "next/link";
import { AgentSelector, AgentOption } from "@/components/agent-selection/agent-selector";

const projectSchema = z.object({
  name: z.string().min(3, "Name must be at least 3 characters").max(100),
  description: z.string().min(10, "Description must be at least 10 characters").max(1000),
  priority: z.enum([Priority.LOW, Priority.MEDIUM, Priority.HIGH, Priority.CRITICAL]),
  selectedAgents: z.array(z.string()).optional().default([]),
});

type ProjectFormData = z.infer<typeof projectSchema>;

// Icon mapping for all agent types
const agentIcons: Record<string, React.ReactNode> = {
  ceo_001: <Target className="h-6 w-6" />,
  cto_001: <Zap className="h-6 w-6" />,
  pm_001: <Users className="h-6 w-6" />,
  backend_001: <Code className="h-6 w-6" />,
  frontend_001: <Palette className="h-6 w-6" />,
  designer_001: <Brain className="h-6 w-6" />,
  hr_monitor_001: <Shield className="h-6 w-6" />,
  cmo_001: <TrendingUp className="h-6 w-6" />,
  content_001: <FileText className="h-6 w-6" />,
  social_media_001: <Users className="h-6 w-6" />,
  cfo_001: <BarChart3 className="h-6 w-6" />,
  financial_analyst_001: <TrendingUp className="h-6 w-6" />,
  sales_manager_001: <Briefcase className="h-6 w-6" />,
  chro_001: <Users className="h-6 w-6" />,
  hr_specialist_001: <Users className="h-6 w-6" />,
  legal_001: <Shield className="h-6 w-6" />,
  research_001: <Lightbulb className="h-6 w-6" />,
  data_analyst_001: <BarChart3 className="h-6 w-6" />,
  coo_001: <Briefcase className="h-6 w-6" />,
};

// Color mapping for all agent types
const agentColors: Record<string, string> = {
  ceo_001: "from-orange-500 to-red-500",
  cto_001: "from-blue-500 to-cyan-500",
  pm_001: "from-purple-500 to-pink-500",
  backend_001: "from-green-500 to-emerald-500",
  frontend_001: "from-pink-500 to-rose-500",
  designer_001: "from-indigo-500 to-purple-500",
  hr_monitor_001: "from-red-500 to-pink-500",
  cmo_001: "from-amber-500 to-orange-500",
  content_001: "from-cyan-500 to-blue-500",
  social_media_001: "from-violet-500 to-purple-500",
  cfo_001: "from-green-500 to-teal-500",
  financial_analyst_001: "from-emerald-500 to-green-500",
  sales_manager_001: "from-sky-500 to-blue-500",
  chro_001: "from-rose-500 to-pink-500",
  hr_specialist_001: "from-fuchsia-500 to-purple-500",
  legal_001: "from-slate-500 to-gray-500",
  research_001: "from-yellow-500 to-amber-500",
  data_analyst_001: "from-violet-500 to-indigo-500",
  coo_001: "from-blue-500 to-indigo-500",
};

export default function CreateProjectPage() {
  const router = useRouter();
  const createProject = useCreateProject();
  const { data: availableAgentsData, isLoading: agentsLoading } = useAvailableAgents();
  const [showSuccess, setShowSuccess] = useState(false);
  const [showError, setShowError] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [createdProjectId, setCreatedProjectId] = useState<string | null>(null);
  const [selectedAgentIds, setSelectedAgentIds] = useState<string[]>([]);

  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
    reset,
    watch,
    setValue,
  } = useForm<ProjectFormData>({
    resolver: zodResolver(projectSchema),
    mode: "onChange",
    defaultValues: {
      priority: Priority.MEDIUM,
      selectedAgents: [],
    },
  });

  const selectedPriority = watch("priority");

  // Transform backend agents to AgentOption format
  const agentOptions = useMemo(() => {
    if (!availableAgentsData) return [];

    return availableAgentsData.map((agent: any) => ({
      id: agent.agent_id || agent.id,
      name: agent.name,
      role: agent.role,
      description: agent.description || "",
      department: agent.department || "General",
      color: agentColors[agent.agent_id || agent.id] || "from-gray-500 to-slate-500",
      icon: agentIcons[agent.agent_id || agent.id] || <Users className="h-6 w-6" />,
      isAvailable: agent.is_available !== false,
      specializations: agent.specializations || [],
    } as AgentOption));
  }, [availableAgentsData]);

  // Handle agent selection changes
  const handleAgentSelection = (newAgentIds: string[]) => {
    setSelectedAgentIds(newAgentIds);
    setValue("selectedAgents", newAgentIds);
  };

  const onSubmit = async (data: ProjectFormData) => {
    try {
      setShowError(false);
      const result = await createProject.mutateAsync(data);
      setCreatedProjectId(result.project_id);
      setShowSuccess(true);

      // Redirect after 3 seconds
      setTimeout(() => {
        router.push(`/projects/${result.project_id}`);
      }, 3000);
    } catch (error: any) {
      console.error("Failed to create project:", error);
      setErrorMessage(error?.message || "Failed to create project. Please try again.");
      setShowError(true);
    }
  };

  if (showSuccess && createdProjectId) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background to-accent/20 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="bg-card rounded-xl border border-border shadow-lg p-8 text-center space-y-6">
            <div className="flex justify-center">
              <div className="relative">
                <div className="absolute inset-0 bg-green-500 rounded-full blur-xl opacity-20 animate-pulse" />
                <CheckCircle2 className="h-20 w-20 text-green-500 relative" />
              </div>
            </div>

            <div className="space-y-2">
              <h2 className="text-3xl font-bold">Project Created!</h2>
              <p className="text-muted-foreground">
                Your project has been submitted to the CEO Agent for evaluation.
              </p>
            </div>

            <div className="bg-accent/50 rounded-lg p-4 space-y-3 text-sm">
              <p className="font-medium flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Timeline
              </p>
              <div className="space-y-2 text-muted-foreground text-left">
                <div className="flex items-start gap-3">
                  <div className="text-green-500 font-bold flex-shrink-0">✓</div>
                  <div>
                    <p className="font-medium text-foreground">CEO Evaluation</p>
                    <p className="text-xs">~15 minutes</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="text-blue-500">→</div>
                  <div>
                    <p className="font-medium text-foreground">Technical Planning</p>
                    <p className="text-xs">~30 minutes</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="text-blue-500">→</div>
                  <div>
                    <p className="font-medium text-foreground">Task Breakdown</p>
                    <p className="text-xs">~45 minutes</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="text-blue-500">→</div>
                  <div>
                    <p className="font-medium text-foreground">Development</p>
                    <p className="text-xs">Parallel execution</p>
                  </div>
                </div>
              </div>
            </div>

            <p className="text-sm text-muted-foreground">
              Redirecting to your project in 3 seconds...
            </p>

            <Button
              onClick={() => router.push(`/projects/${createdProjectId}`)}
              className="w-full"
            >
              Go to Project Now
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-accent/10">
      {/* Header */}
      <div className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link
            href="/projects"
            className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
            <span>Back to Projects</span>
          </Link>
          <h1 className="text-2xl font-bold">Create New Project</h1>
          <div className="w-20" />
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
          {/* Form Section */}
          <div className="lg:col-span-2 space-y-8">
            {/* Error Alert */}
            {showError && (
              <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4 flex gap-3">
                <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-destructive">Error Creating Project</p>
                  <p className="text-sm text-destructive/80">{errorMessage}</p>
                </div>
              </div>
            )}

            {/* Form Card */}
            <div className="bg-card rounded-xl border border-border shadow-sm">
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-8 p-8">
                {/* Project Name */}
                <div className="space-y-3">
                  <div>
                    <label htmlFor="name" className="text-sm font-semibold text-foreground">
                      Project Name <span className="text-red-500">*</span>
                    </label>
                    <p className="text-xs text-muted-foreground mt-1">
                      Give your project a clear, descriptive name
                    </p>
                  </div>
                  <input
                    {...register("name")}
                    id="name"
                    type="text"
                    placeholder="e.g., Modern Todo List Application"
                    className="w-full px-4 py-3 border rounded-lg bg-background/50 focus:outline-none focus:ring-2 focus:ring-primary/50 border-border/50 focus:border-primary transition-all"
                  />
                  {errors.name && (
                    <p className="text-sm text-red-500 flex items-center gap-1">
                      <AlertCircle className="h-4 w-4" />
                      {errors.name.message}
                    </p>
                  )}
                </div>

                {/* Description */}
                <div className="space-y-3">
                  <div>
                    <label htmlFor="description" className="text-sm font-semibold text-foreground">
                      Project Description <span className="text-red-500">*</span>
                    </label>
                    <p className="text-xs text-muted-foreground mt-1">
                      Describe your project in detail. Include features, requirements, target users, and technologies.
                    </p>
                  </div>
                  <textarea
                    {...register("description")}
                    id="description"
                    rows={7}
                    placeholder="Example: Build a collaborative todo list app with real-time syncing. Features include task management, team collaboration, recurring tasks, and integrations with calendar apps. Built with React frontend and Node.js backend..."
                    className="w-full px-4 py-3 border rounded-lg bg-background/50 focus:outline-none focus:ring-2 focus:ring-primary/50 border-border/50 focus:border-primary transition-all resize-none"
                  />
                  {errors.description && (
                    <p className="text-sm text-red-500 flex items-center gap-1">
                      <AlertCircle className="h-4 w-4" />
                      {errors.description.message}
                    </p>
                  )}
                  <p className="text-xs text-muted-foreground">
                    The more detailed your description, the better the agents can understand and execute your vision.
                  </p>
                </div>

                {/* Priority */}
                <div className="space-y-3">
                  <div>
                    <label htmlFor="priority" className="text-sm font-semibold text-foreground">
                      Priority Level
                    </label>
                    <p className="text-xs text-muted-foreground mt-1">
                      Set the priority to control when agents start working on your project
                    </p>
                  </div>
                  <div className="grid grid-cols-4 gap-3">
                    {[
                      { value: Priority.LOW, label: "Low", icon: "🟢" },
                      { value: Priority.MEDIUM, label: "Medium", icon: "🟡" },
                      { value: Priority.HIGH, label: "High", icon: "🟠" },
                      { value: Priority.CRITICAL, label: "Critical", icon: "🔴" },
                    ].map((option) => (
                      <label key={option.value} className="cursor-pointer">
                        <input
                          type="radio"
                          {...register("priority")}
                          value={option.value}
                          className="hidden"
                        />
                        <div className={`p-3 rounded-lg border-2 transition-all text-center hover:border-primary/50 ${
                          selectedPriority === option.value
                            ? "border-primary bg-primary/5"
                            : "border-border/50"
                        }`}>
                          <div className="text-2xl mb-1">{option.icon}</div>
                          <p className="text-xs font-medium">{option.label}</p>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Agent Selection */}
                <div className="space-y-3 pt-4 border-t border-border/50">
                  <div>
                    <label className="text-sm font-semibold text-foreground">
                      Select Your Agent Team (Optional)
                    </label>
                    <p className="text-xs text-muted-foreground mt-1">
                      Choose specialized agents to collaborate on your project. Filter by department or search by name. Let the CEO agent lead if you don't select any.
                    </p>
                  </div>
                  {agentsLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    </div>
                  ) : (
                    <AgentSelector
                      agents={agentOptions}
                      selectedAgents={selectedAgentIds}
                      onSelectionChange={handleAgentSelection}
                      searchPlaceholder="Search agents by name, role, or department..."
                      showDepartmentFilter={true}
                    />
                  )}
                </div>

                {/* Submit Button */}
                <div className="flex gap-3 pt-6 border-t border-border/50">
                  <Link href="/projects" className="flex-1">
                    <Button
                      type="button"
                      variant="outline"
                      className="w-full"
                      disabled={createProject.isPending}
                    >
                      Cancel
                    </Button>
                  </Link>
                  <Button
                    type="submit"
                    disabled={createProject.isPending || !isValid}
                    className="flex-1"
                  >
                    {createProject.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Creating Project...
                      </>
                    ) : (
                      "Create Project"
                    )}
                  </Button>
                </div>
              </form>
            </div>
          </div>

          {/* Sidebar - Info & Benefits */}
          <div className="space-y-6">
            {/* What Happens Next */}
            <div className="bg-card rounded-xl border border-border shadow-sm p-6 space-y-4">
              <h3 className="font-semibold text-lg flex items-center gap-2">
                <Clock className="h-5 w-5 text-primary" />
                What Happens Next?
              </h3>
              <div className="space-y-4">
                <div className="flex gap-3">
                  <div className="flex-shrink-0">
                    <div className="flex items-center justify-center h-8 w-8 rounded-full bg-primary/20 text-primary font-semibold text-sm">
                      1
                    </div>
                  </div>
                  <div>
                    <p className="font-medium text-sm">CEO Review</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Evaluates feasibility (~15 min)
                    </p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <div className="flex-shrink-0">
                    <div className="flex items-center justify-center h-8 w-8 rounded-full bg-blue-500/20 text-blue-500 font-semibold text-sm">
                      2
                    </div>
                  </div>
                  <div>
                    <p className="font-medium text-sm">Technical Planning</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      CTO designs architecture (~30 min)
                    </p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <div className="flex-shrink-0">
                    <div className="flex items-center justify-center h-8 w-8 rounded-full bg-purple-500/20 text-purple-500 font-semibold text-sm">
                      3
                    </div>
                  </div>
                  <div>
                    <p className="font-medium text-sm">Task Breakdown</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      PM creates task list (~45 min)
                    </p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <div className="flex-shrink-0">
                    <div className="flex items-center justify-center h-8 w-8 rounded-full bg-green-500/20 text-green-500 font-semibold text-sm">
                      4
                    </div>
                  </div>
                  <div>
                    <p className="font-medium text-sm">Development</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Agents collaborate and build (~2+ hours)
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Tips */}
            <div className="bg-accent/50 rounded-xl border border-border/50 p-6 space-y-4">
              <h3 className="font-semibold text-lg">💡 Tips for Success</h3>
              <ul className="space-y-3 text-sm">
                <li className="flex gap-2">
                  <span className="text-primary">✓</span>
                  <span>Be specific about your requirements and goals</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-primary">✓</span>
                  <span>Mention target users and use cases</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-primary">✓</span>
                  <span>Suggest technologies if you have preferences</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-primary">✓</span>
                  <span>Set appropriate priority based on urgency</span>
                </li>
              </ul>
            </div>

            {/* Agent Team */}
            <div className="bg-card rounded-xl border border-border shadow-sm p-6 space-y-4">
              <h3 className="font-semibold text-lg">🤖 Available Agents</h3>
              <p className="text-xs text-muted-foreground">
                We have {agentOptions.length} specialized agents across {new Set(agentOptions.map(a => a.department)).size} departments.
              </p>
              {agentOptions.length > 0 && (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {agentOptions.slice(0, 8).map((agent) => (
                    <div key={agent.id} className="flex items-start gap-2 pb-2 border-b last:border-b-0">
                      <div className={`inline-block p-2 rounded-md bg-gradient-to-br ${agent.color} text-white flex-shrink-0`}>
                        {agent.icon}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium">{agent.name}</p>
                        <p className="text-xs text-muted-foreground">{agent.role}</p>
                      </div>
                      {selectedAgentIds.includes(agent.id) && (
                        <div className="text-primary text-xs font-bold">✓</div>
                      )}
                    </div>
                  ))}
                  {agentOptions.length > 8 && (
                    <p className="text-xs text-muted-foreground text-center pt-2">
                      +{agentOptions.length - 8} more agents
                    </p>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
