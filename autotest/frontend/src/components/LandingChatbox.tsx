import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from './ui/card';
import { Textarea } from './ui/textarea';
import { Button } from './ui/button';
import { Play } from 'lucide-react';
import { BorderBeam } from "@/components/magicui/border-beam";
import { agentApi } from '@/services/api.tsx';
import { ShineBorder } from "@/components/magicui/shine-border";



const LandingChatbox: React.FC = () => {
  const [task, setTask] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  // Listen for external fill requests
  useEffect(() => {
    const container = document.getElementById('landing-chatbox');
    if (!container) return;
    const handler = (event: Event) => {
      const customEvent = event as CustomEvent<{ text: string }>;
      setTask(customEvent.detail.text);
    };
    container.addEventListener('fillChatInput', handler);
    return () => {
      container.removeEventListener('fillChatInput', handler);
    };
  }, []);

  const handleRun = async () => {
    if (!task.trim() || isLoading) return;
    
    setIsLoading(true);
    try {
      // Create a new agent
      const response = await agentApi.createAgent();
      const agentId = response.data.agent_id;
      
      // Store the prompt and agent ID in localStorage
      localStorage.setItem('pendingPrompt', task);
      localStorage.setItem('pendingAgentId', agentId);
      
      // Redirect to the main app
      navigate('/app');
    } catch (error) {
      console.error('Error creating agent:', error);
      
      // Check if it's a connection error (likely API server not running)
      if (error.message && error.message.includes('Network Error')) {
        alert('Failed to connect to the backend server. Please ensure the API server is running on port 9000.');
      } else if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        alert(`Server error: ${error.response.status} - ${error.response.data.detail || 'Unknown error'}`);
      } else {
        // Something happened in setting up the request that triggered an Error
        alert('Failed to create agent. Please try again later.');
      }
      
      setIsLoading(false);
    }
  };

  return (
    <Card id="landing-chatbox" className="relative w-full mb-6 overflow-hidden">
        <ShineBorder shineColor={["#A07CFE", "#FE8FB5", "#FFBE7B"]} />
      <CardContent className="p-2 relative">
     
        <Textarea
          placeholder="Describe the task you want to test..."
          value={task}
          onChange={(e) => setTask(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleRun();
            }
          }}
          rows={3}
          className="border-none focus:border-none focus:ring-0 focus:outline-none resize-none"
          disabled={isLoading}
        />
                 <div className="relative">
          <Button 
            onClick={handleRun} 
            variant="ghost" 
            className="absolute bottom-0 right-0 w-10 h-10 border border-gray-300 rounded-full flex items-center justify-center"
            disabled={!task.trim() || isLoading}
          >
            <Play className="h-6 w-6" />
          </Button>
        </div>
      
      </CardContent>
    </Card>
  );
};

export default LandingChatbox;
