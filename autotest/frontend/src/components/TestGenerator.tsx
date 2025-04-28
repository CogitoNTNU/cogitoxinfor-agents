import React, { useState } from 'react';
import MonacoEditor from '@monaco-editor/react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Copy, Play } from 'lucide-react'; // Import Copy and Play icons
import { RainbowButton } from "@/components/magicui/rainbow-button";

const TestGenerator: React.FC = () => {
  const [script, setScript] = useState<string>('');
  const [output, setOutput] = useState<string>('');
  const [loadingGen, setLoadingGen] = useState<boolean>(false);
  const [running, setRunning] = useState<boolean>(false);

  // TODO: replace with dynamic agent_id or pass via props/env
  const agentId = '1dd8280a-c424-4e43-a27b-a161fda485a2';

  const generateTest = async () => {
    setLoadingGen(true);
    try {
      const res = await fetch(`/api/generate?agent_id=${agentId}`);
      const { script } = await res.json();
      setScript(script);
    } catch (err) {
      console.error('Error generating test:', err);
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
      const { output } = await res.json();
      setOutput(output);
    } catch (err) {
      console.error('Error running test:', err);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="flex flex-col h-full w-full max-w-2xl mx-auto">
      <RainbowButton
        className="mb-4 mt-4 self-center"
        onClick={generateTest}
        disabled={loadingGen}
      >
        {loadingGen ? 'Generating…' : 'Generate test'}
      </RainbowButton>
      <Card className="w-full flex-1">
        <CardHeader className="flex items-center justify-between">
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
        <CardContent className="flex flex-col">
          <div className="h-80 mb-4">
            <MonacoEditor
              height="100%"
              defaultLanguage="python"
              value={script}
              onChange={(value) => setScript(value || '')}
            />
          </div>
          {output && (
            <pre className="bg-gray-800 text-white p-4 rounded-md overflow-auto flex-1">
              {output}
            </pre>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default TestGenerator;
