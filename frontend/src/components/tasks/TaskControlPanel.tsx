/**
 * Task Control Panel Component - Phase 2
 *
 * Provides user controls for task execution:
 * - Pause/Resume functionality
 * - Cancel with reason
 * - Add context hints
 * - View control status
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import {
  Pause,
  Play,
  X,
  Plus,
  Clock,
  AlertCircle,
  CheckCircle,
  Loader2,
} from 'lucide-react';
import { useToast } from '@/components/error/error-toast';

interface TaskControlPanelProps {
  taskId: string;
  taskTitle: string;
  onPause?: () => void;
  onResume?: () => void;
  onCancel?: () => void;
}

interface ControlStatus {
  task_id: string;
  is_paused: boolean;
  pause_reason: string | null;
  paused_at: string | null;
  user_context: string | null;
  can_pause: boolean;
  can_resume: boolean;
  can_cancel: boolean;
}

export function TaskControlPanel({
  taskId,
  taskTitle,
  onPause,
  onResume,
  onCancel,
}: TaskControlPanelProps) {
  const [status, setStatus] = useState<ControlStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionInProgress, setActionInProgress] = useState(false);
  const [pauseReason, setPauseReason] = useState('');
  const [cancelReason, setCancelReason] = useState('');
  const [contextInput, setContextInput] = useState('');
  const [addingContext, setAddingContext] = useState(false);
  const { toast } = useToast();

  // Fetch control status
  useEffect(() => {
    fetchControlStatus();
    const interval = setInterval(fetchControlStatus, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, [taskId]);

  const fetchControlStatus = async () => {
    try {
      const response = await fetch(
        `/api/v1/tasks/${taskId}/control-status`
      );
      if (!response.ok) throw new Error('Failed to fetch control status');
      const data = await response.json();
      setStatus(data);
    } catch (error) {
      console.error('Error fetching control status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePause = async () => {
    setActionInProgress(true);
    try {
      const response = await fetch(
        `/api/v1/tasks/${taskId}/pause`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            reason: pauseReason || 'Paused by user',
          }),
        }
      );

      if (!response.ok) throw new Error('Failed to pause task');
      const result = await response.json();

      toast({
        title: 'Success',
        description: result.message,
      });

      setPauseReason('');
      await fetchControlStatus();
      onPause?.();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to pause task',
        variant: 'destructive',
      });
      console.error('Error pausing task:', error);
    } finally {
      setActionInProgress(false);
    }
  };

  const handleResume = async () => {
    setActionInProgress(true);
    try {
      const response = await fetch(
        `/api/v1/tasks/${taskId}/resume`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) throw new Error('Failed to resume task');
      const result = await response.json();

      toast({
        title: 'Success',
        description: result.message,
      });

      await fetchControlStatus();
      onResume?.();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to resume task',
        variant: 'destructive',
      });
      console.error('Error resuming task:', error);
    } finally {
      setActionInProgress(false);
    }
  };

  const handleCancel = async () => {
    setActionInProgress(true);
    try {
      const response = await fetch(
        `/api/v1/tasks/${taskId}/cancel`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            reason: cancelReason || 'Cancelled by user',
          }),
        }
      );

      if (!response.ok) throw new Error('Failed to cancel task');
      const result = await response.json();

      toast({
        title: 'Success',
        description: result.message,
      });

      setCancelReason('');
      await fetchControlStatus();
      onCancel?.();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to cancel task',
        variant: 'destructive',
      });
      console.error('Error cancelling task:', error);
    } finally {
      setActionInProgress(false);
    }
  };

  const handleAddContext = async () => {
    if (!contextInput.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter some context',
        variant: 'destructive',
      });
      return;
    }

    setAddingContext(true);
    try {
      const response = await fetch(
        `/api/v1/tasks/${taskId}/context`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            context: contextInput,
          }),
        }
      );

      if (!response.ok) throw new Error('Failed to add context');
      const result = await response.json();

      toast({
        title: 'Success',
        description: result.message,
      });

      setContextInput('');
      await fetchControlStatus();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to add context',
        variant: 'destructive',
      });
      console.error('Error adding context:', error);
    } finally {
      setAddingContext(false);
    }
  };

  if (loading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Task Controls</CardTitle>
          <CardDescription>{taskTitle}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!status) {
    return (
      <Card className="w-full border-red-200 bg-red-50">
        <CardHeader>
          <CardTitle className="text-red-900">Task Controls</CardTitle>
          <CardDescription className="text-red-800">
            Failed to load control status
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Task Controls</CardTitle>
            <CardDescription>{taskTitle}</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {status.is_paused ? (
              <div className="flex items-center gap-1 rounded-full bg-yellow-100 px-3 py-1 text-sm text-yellow-800">
                <AlertCircle className="h-4 w-4" />
                Paused
              </div>
            ) : (
              <div className="flex items-center gap-1 rounded-full bg-green-100 px-3 py-1 text-sm text-green-800">
                <CheckCircle className="h-4 w-4" />
                Running
              </div>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Status Section */}
        <div className="space-y-2 rounded-lg bg-slate-50 p-4">
          <h3 className="font-semibold text-sm">Status Information</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">State</p>
              <p className="font-medium">
                {status.is_paused ? 'Paused' : 'Running'}
              </p>
            </div>
            {status.paused_at && (
              <div>
                <p className="text-muted-foreground">Paused At</p>
                <p className="font-medium text-sm">
                  {new Date(status.paused_at).toLocaleString()}
                </p>
              </div>
            )}
            {status.pause_reason && (
              <div className="col-span-2">
                <p className="text-muted-foreground">Pause Reason</p>
                <p className="font-medium">{status.pause_reason}</p>
              </div>
            )}
          </div>
        </div>

        {/* Control Actions */}
        <div className="space-y-3">
          <h3 className="font-semibold text-sm">Control Actions</h3>
          <div className="grid grid-cols-2 gap-3">
            {/* Pause Button */}
            {status.can_pause && (
              <Button
                onClick={handlePause}
                disabled={actionInProgress}
                variant="outline"
                className="gap-2"
              >
                {actionInProgress ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Pause className="h-4 w-4" />
                )}
                Pause
              </Button>
            )}

            {/* Resume Button */}
            {status.can_resume && (
              <Button
                onClick={handleResume}
                disabled={actionInProgress}
                variant="outline"
                className="gap-2"
              >
                {actionInProgress ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
                Resume
              </Button>
            )}

            {/* Cancel Button */}
            {status.can_cancel && (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button
                    disabled={actionInProgress}
                    variant="destructive"
                    className="gap-2"
                  >
                    <X className="h-4 w-4" />
                    Cancel Task
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogTitle>Cancel Task?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This action cannot be undone. The task will be marked as
                    cancelled.
                  </AlertDialogDescription>
                  <div className="mt-4">
                    <label className="text-sm font-medium">Reason (optional)</label>
                    <Input
                      placeholder="Why are you cancelling this task?"
                      value={cancelReason}
                      onChange={(e) => setCancelReason(e.target.value)}
                      className="mt-2"
                    />
                  </div>
                  <div className="flex gap-3">
                    <AlertDialogCancel>Keep Task</AlertDialogCancel>
                    <AlertDialogAction
                      onClick={handleCancel}
                      className="bg-red-600 hover:bg-red-700"
                    >
                      Cancel Task
                    </AlertDialogAction>
                  </div>
                </AlertDialogContent>
              </AlertDialog>
            )}
          </div>
        </div>

        {/* Pause Reason Input */}
        {status.can_pause && !status.is_paused && (
          <div className="space-y-2">
            <label className="text-sm font-medium">Pause Reason (optional)</label>
            <Input
              placeholder="Why are you pausing this task?"
              value={pauseReason}
              onChange={(e) => setPauseReason(e.target.value)}
            />
          </div>
        )}

        {/* User Context Section */}
        <div className="space-y-3 border-t pt-4">
          <h3 className="font-semibold text-sm">Add Context Hints</h3>
          <p className="text-sm text-muted-foreground">
            Provide guidance to help the agent make better decisions
          </p>
          <Textarea
            placeholder="Enter context, constraints, or hints to guide the agent..."
            value={contextInput}
            onChange={(e) => setContextInput(e.target.value)}
            rows={4}
          />
          <Button
            onClick={handleAddContext}
            disabled={addingContext || !contextInput.trim()}
            className="w-full gap-2"
          >
            {addingContext ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Plus className="h-4 w-4" />
            )}
            Add Context
          </Button>
        </div>

        {/* Current Context Display */}
        {status.user_context && (
          <div className="space-y-2 rounded-lg bg-blue-50 p-4">
            <h3 className="font-semibold text-sm text-blue-900">Current Context</h3>
            <p className="text-sm text-blue-800 whitespace-pre-wrap">
              {status.user_context}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
