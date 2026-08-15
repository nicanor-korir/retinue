import { Card, CardContent } from "@/components/ui/card";
import { LucideIcon } from "lucide-react";
import { ReactNode } from "react";

interface EmptyStateProps {
  /** Icon to display */
  icon: LucideIcon;
  /** Title text */
  title: string;
  /** Description text */
  description?: string;
  /** Optional action buttons or links */
  action?: ReactNode;
  /** Whether to wrap in Card (default: true) */
  withCard?: boolean;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  withCard = true
}: EmptyStateProps) {
  const content = (
    <CardContent className="flex flex-col items-center justify-center py-16">
      <Icon className="h-16 w-16 text-muted-foreground mb-4" />
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      {description && (
        <p className="text-muted-foreground text-center max-w-md mb-4">
          {description}
        </p>
      )}
      {action}
    </CardContent>
  );

  if (withCard) {
    return <Card>{content}</Card>;
  }

  return content;
}
