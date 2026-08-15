import { DashboardLayout } from "@/components/layout/dashboard-layout";

interface LoadingStateProps {
  /** Optional custom loading text */
  text?: string;
  /** Whether to wrap in DashboardLayout (default: true) */
  withLayout?: boolean;
  /** Optional custom spinner size */
  size?: "sm" | "md" | "lg";
}

const spinnerSizes = {
  sm: "h-8 w-8",
  md: "h-12 w-12",
  lg: "h-16 w-16",
};

export function LoadingState({ text, withLayout = true, size = "md" }: LoadingStateProps) {
  const spinner = (
    <div className="flex flex-col items-center justify-center h-96 gap-4">
      <div className={`animate-spin rounded-full border-b-2 border-primary ${spinnerSizes[size]}`} />
      {text && <p className="text-muted-foreground text-sm">{text}</p>}
    </div>
  );

  if (withLayout) {
    return <DashboardLayout>{spinner}</DashboardLayout>;
  }

  return spinner;
}
