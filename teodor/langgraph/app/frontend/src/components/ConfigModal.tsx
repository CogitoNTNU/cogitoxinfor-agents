
import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Checkbox } from './ui/checkbox';
import { toast } from "sonner";

interface ConfigModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const ConfigModal: React.FC<ConfigModalProps> = ({ open, onOpenChange }) => {
  const [config, setConfig] = useState({
    apiUrl: 'http://localhost:8000',
    backendFolder: '/images',
    allowInterrupts: true,
    debugMode: false,
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setConfig(prev => ({ ...prev, [name]: value }));
  };

  const handleCheckboxChange = (name: string, checked: boolean) => {
    setConfig(prev => ({ ...prev, [name]: checked }));
  };

  const handleSave = () => {
    localStorage.setItem('agentConfig', JSON.stringify(config));
    toast.success("Configuration saved", {
      description: "Your settings have been updated"
    });
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Agent Configuration</DialogTitle>
          <DialogDescription>
            Configure how the agent works and interacts with the backend
          </DialogDescription>
        </DialogHeader>
        
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="apiUrl">API URL</Label>
            <Input
              id="apiUrl"
              name="apiUrl"
              value={config.apiUrl}
              onChange={handleChange}
            />
          </div>
          
          <div className="grid gap-2">
            <Label htmlFor="backendFolder">Backend Images Path</Label>
            <Input
              id="backendFolder"
              name="backendFolder"
              value={config.backendFolder}
              onChange={handleChange}
            />
          </div>
          
          <div className="flex items-center space-x-2">
            <Checkbox
              id="allowInterrupts"
              checked={config.allowInterrupts}
              onCheckedChange={(checked) => 
                handleCheckboxChange('allowInterrupts', checked as boolean)
              }
            />
            <Label htmlFor="allowInterrupts">Allow agent interrupts</Label>
          </div>
          
          <div className="flex items-center space-x-2">
            <Checkbox
              id="debugMode"
              checked={config.debugMode}
              onCheckedChange={(checked) => 
                handleCheckboxChange('debugMode', checked as boolean)
              }
            />
            <Label htmlFor="debugMode">Debug mode</Label>
          </div>
        </div>
        
        <DialogFooter>
          <Button onClick={handleSave}>Save changes</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
