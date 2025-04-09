
import React, { useState } from 'react';
import { useAgent } from '../context/AgentContext';
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
import { AlertTriangle } from 'lucide-react';

export const InterruptDialog: React.FC = () => {
  const { interruptMessage, respondToInterrupt } = useAgent();
  const [customInput, setCustomInput] = useState('');

  const handleApprove = () => {
    respondToInterrupt('');
  };

  const handleSubmitCustom = () => {
    respondToInterrupt(customInput);
    setCustomInput('');
  };

  return (
    <Dialog open={!!interruptMessage} onOpenChange={() => {}}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-agent-interrupt" />
            Agent Needs Input
          </DialogTitle>
          <DialogDescription>
            The agent is requesting your approval or alternative instructions.
          </DialogDescription>
        </DialogHeader>
        
        <div className="p-4 my-2 bg-muted/50 rounded border text-sm">
          {interruptMessage}
        </div>
        
        <div className="space-y-2">
          <Input
            value={customInput}
            onChange={(e) => setCustomInput(e.target.value)}
            placeholder="Provide custom instructions (optional)"
            className="w-full"
          />
        </div>
        
        <DialogFooter className="flex flex-col sm:flex-row gap-2 sm:gap-0">
          <Button 
            variant="default" 
            onClick={handleApprove}
            className="w-full sm:w-auto"
          >
            Approve Default Action
          </Button>
          <Button 
            variant="outline" 
            onClick={handleSubmitCustom}
            disabled={!customInput.trim()}
            className="w-full sm:w-auto"
          >
            Send Custom Instructions
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
