import { ReactNode } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { AlertTriangle, CheckCircle, Info, XCircle } from "lucide-react";

type ConfirmDialogVariant = "default" | "destructive" | "warning" | "success";

interface ConfirmDialogProps {
  /** Whether dialog is open */
  open: boolean;
  /** Callback when dialog open state changes */
  onOpenChange: (open: boolean) => void;
  /** Dialog title */
  title: string;
  /** Dialog description */
  description: string;
  /** Confirm button text */
  confirmText?: string;
  /** Cancel button text */
  cancelText?: string;
  /** Callback when confirmed */
  onConfirm: () => void | Promise<void>;
  /** Whether action is loading */
  isLoading?: boolean;
  /** Dialog variant affects button styling */
  variant?: ConfirmDialogVariant;
  /** Optional additional content */
  children?: ReactNode;
}

const variantConfig = {
  default: {
    icon: Info,
    iconColor: "text-blue-500",
    bgColor: "bg-blue-50 border-blue-200",
    buttonClass: "bg-blue-600 hover:bg-blue-700",
  },
  destructive: {
    icon: XCircle,
    iconColor: "text-red-500",
    bgColor: "bg-destructive/10 border-destructive/20",
    buttonClass: "",
  },
  warning: {
    icon: AlertTriangle,
    iconColor: "text-orange-500",
    bgColor: "bg-orange-50 border-orange-200",
    buttonClass: "bg-orange-600 hover:bg-orange-700",
  },
  success: {
    icon: CheckCircle,
    iconColor: "text-green-500",
    bgColor: "bg-green-50 border-green-200",
    buttonClass: "bg-green-600 hover:bg-green-700",
  },
};

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmText = "Confirm",
  cancelText = "Cancel",
  onConfirm,
  isLoading = false,
  variant = "default",
  children,
}: ConfirmDialogProps) {
  const config = variantConfig[variant];
  const Icon = config.icon;

  const handleConfirm = async () => {
    await onConfirm();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Icon className={`h-5 w-5 ${config.iconColor}`} />
            {title}
          </DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        {children}
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isLoading}
          >
            {cancelText}
          </Button>
          <Button
            variant={variant === "destructive" ? "destructive" : "default"}
            className={variant !== "destructive" ? config.buttonClass : ""}
            onClick={handleConfirm}
            disabled={isLoading}
          >
            {isLoading ? "Processing..." : confirmText}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
