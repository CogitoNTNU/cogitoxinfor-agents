import React, { useState, useEffect } from 'react';
import MonacoEditor from '@monaco-editor/react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Copy, Play, Info } from 'lucide-react'; // Import Copy, Play, and Info icons
import { RainbowButton } from "@/components/magicui/rainbow-button";
import { useAgent } from '../context/AgentContext';
import { BlurFade } from './magicui/blur-fade';
import { Toggle } from "@/components/ui/toggle";

const TestGenerator: React.FC = () => {
  const [script, setScript] = useState<string>('');
  const [output, setOutput] = useState<string>('');
  const [loadingGen, setLoadingGen] = useState<boolean>(false);
  const [running, setRunning] = useState<boolean>(false);
  const [inforMode, setInforMode] = useState<boolean>(localStorage.getItem('inforMode') === 'true');
  
  // Update localStorage when inforMode changes
  useEffect(() => {
    localStorage.setItem('inforMode', inforMode ? 'true' : 'false');
    console.log(`Infor mode ${inforMode ? 'enabled' : 'disabled'}, saved to localStorage`);
  }, [inforMode]);
  const { currentAgentId, actionHistory } = useAgent();

  const generateTest = async () => {
    if (!currentAgentId) return;
    
    console.log("Generating test for agent:", currentAgentId);
    console.log("Using infor mode:", inforMode);
    setLoadingGen(true);
    try {
      const url = `/api/generate?agentId=${currentAgentId}&mode=${inforMode ? 'infor' : 'regular'}`;
      console.log("Fetching from URL:", url);
      const res = await fetch(url);
      
      if (!res.ok) {
        // Handle HTTP error responses
        const errorText = await res.text();
        console.error(`Error response (${res.status}):`, errorText);
        throw new Error(`API error: ${res.status} - ${errorText || 'Unknown error'}`);
      }
      
      console.log("Response status:", res.status);
      const scriptText = await res.text();
      
      if (!scriptText || scriptText.trim() === '') {
        throw new Error('Received empty response from the API');
      }
      
      console.log("Received script text:", scriptText.substring(0, 100) + "...");
      setScript(scriptText);
    } catch (err) {
      console.error('Error generating test:', err);
      alert(`Failed to generate test: ${err.message || 'API server may not be running. Check if the API server is running on port 9000.'}`);
    } finally {
      setLoadingGen(false);
    }
  };

  const runTest = async () => {
    setRunning(true);
    try {
      const res = await fetch('/api/run-test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ script }),
      });
      
      if (!res.ok) {
        // Handle HTTP error responses
        const errorText = await res.text();
        console.error(`Error response (${res.status}):`, errorText);
        throw new Error(`API error: ${res.status} - ${errorText || 'Unknown error'}`);
      }
      
      const output = await res.text();
      setOutput(output || 'No output received from test run');
    } catch (err) {
      console.error('Error running test:', err);
      setOutput(`Error running test: ${err.message || 'API server may not be running. Check if the API server is running on port 9000.'}`);
      alert(`Failed to run test: ${err.message || 'API server may not be running. Check if the API server is running on port 9000.'}`);
    } finally {
      setRunning(false);
    }
  };

  // Only check if agent is selected, since we know the agent has logs on the backend
  // This bypasses the actionHistory check which might not be properly populated
  console.log("TestGenerator - currentAgentId:", currentAgentId);
  console.log("TestGenerator - actionHistory:", actionHistory);
  
  const canGenerateTest = !!currentAgentId;

  return (
    <div className="flex flex-col h-[40rem] w-[70rem] mx-auto">
      <div className="flex flex-col items-center mb-8 mt-8">
        <div className="flex items-center mb-4">
          <Toggle 
            className="mr-2 data-[state=on]:bg-blue-100"
            pressed={inforMode}
            onPressedChange={setInforMode}
            title="Toggle Infor Mode"
            aria-label="Toggle Infor Mode"
          >
            <Info className="h-4 w-4 mr-2" />
            Infor Mode
          </Toggle>
        </div>
        <RainbowButton
          className="self-center"
          onClick={generateTest}
          disabled={loadingGen || !canGenerateTest}
        >
          {loadingGen ? 'Generating…' : 'Generate test'}
        </RainbowButton>
      </div>
      {script ? (

        <div className="flex flex-row gap-4 flex-1 overflow-hidden">
          <BlurFade delay={0.25} inView className="w-1/2 flex-1 flex flex-col overflow-hidden">
        {/* Left side - Code Editor */}
        <Card className="h-full flex flex-col">
          <CardHeader className="flex items-center justify-between py-2">
            <CardTitle>Test Script</CardTitle>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="icon"
                onClick={() => navigator.clipboard.writeText(script)}
                disabled={!script}
              >
                <Copy className="h-4 w-4" />
              </Button>
              <Button
                className="bg-green-500 hover:bg-green-600"
                onClick={runTest}
                disabled={!script || running}
              >
                <Play className="h-4 w-4 mr-2" />
                {running ? 'Running…' : 'Run Test'}
              </Button>
            </div>
          </CardHeader>
          <CardContent className="flex-1 overflow-hidden p-2">
            <div className="h-full w-full">
              <MonacoEditor
                height="100%"
                defaultLanguage="python"
                value={script}
                onChange={(value) => setScript(value || '')}
                options={{
                  scrollBeyondLastLine: false,
                  minimap: { enabled: false }
                }}
              />
            </div>
          </CardContent>
        </Card>
          </BlurFade>
          <BlurFade delay={0.30} inView className="w-1/2 flex-1 flex flex-col overflow-auto">
        {/* Right side - Terminal Output */}
        <Card className="h-full flex flex-col">
          <CardHeader className="py-2">
            <CardTitle>Terminal Output</CardTitle>
          </CardHeader>
          <CardContent className="flex-1 overflow-auto p-2">
            <div className="h-full w-full">
              {output ? (
                <pre className="bg-gray-800 text-white text-[10px] p-4 rounded-md overflow-hidden w-100 h-[40]">
                  {output}
                </pre>
              ) : (
                <div className="flex items-center justify-center h-full bg-gray-800 text-gray-400 rounded-md">
                  <p>Run the test to see output here</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
          </BlurFade>
        </div>
      ) : (
      <div>
      </div>
      )}
    </div>
  );
};

export default TestGenerator;
