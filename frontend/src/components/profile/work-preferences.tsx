"use client";

import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface WorkPreferencesProps {
  onSettingsChange?: (updates: Record<string, any>) => void;
}

export function WorkPreferences({ onSettingsChange }: WorkPreferencesProps) {
  const handleChange = () => {
    onSettingsChange?.({});
  };

  return (
    <Card className="p-6">
      <h2 className="text-xl font-semibold mb-6">Work Preferences</h2>
      <div className="space-y-6">
        <div className="space-y-4">
          <Label>Working Hours</Label>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-sm text-muted-foreground">Start Time</Label>
              <Input type="time" defaultValue="09:00" onChange={() => handleChange()} />
            </div>
            <div>
              <Label className="text-sm text-muted-foreground">End Time</Label>
              <Input type="time" defaultValue="17:00" onChange={() => handleChange()} />
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <Label>Default Task View</Label>
          <Select defaultValue="list" onValueChange={() => handleChange()}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="list">List View</SelectItem>
              <SelectItem value="board">Board View</SelectItem>
              <SelectItem value="calendar">Calendar View</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Availability Status</Label>
          <Select defaultValue="available" onValueChange={() => handleChange()}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="available">Available</SelectItem>
              <SelectItem value="busy">Busy</SelectItem>
              <SelectItem value="away">Away</SelectItem>
              <SelectItem value="dnd">Do Not Disturb</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
    </Card>
  );
}
