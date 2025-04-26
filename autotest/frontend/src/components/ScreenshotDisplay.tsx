import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { Trash2, Maximize2, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';

interface Screenshot {
  step: number;
  image: string;
  timestamp: number;
}

interface ScreenshotDisplayProps {
  screenshots: Screenshot[];
  onClearScreenshots: () => void;
  className?: string;
  loading?: boolean;
}

export const ScreenshotDisplay: React.FC<ScreenshotDisplayProps> = ({
  screenshots,
  onClearScreenshots,
  className,
  loading
}) => {
  const [selectedScreenshot, setSelectedScreenshot] = useState<Screenshot | null>(null);

  // Function to format the timestamp
  const formatTimestamp = (timestamp: number) => {
    return format(new Date(timestamp), 'HH:mm:ss');
  };

  return (
    <>
      <Card className={cn("w-full", className)}>
        <CardHeader className="p-4 pb-2 flex flex-row items-center justify-between">
          <CardTitle className="text-lg">Screenshots</CardTitle>
          {screenshots.length > 0 && (
            <Button 
              variant="outline" 
              size="sm" 
              onClick={onClearScreenshots}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Clear Screenshots
            </Button>
          )}
        </CardHeader>
        <CardContent className="p-4">
          {screenshots.length === 0 ? (
            <div className="flex items-center justify-center h-[300px] border border-dashed rounded-md">
              <p className="text-muted-foreground">No screenshots available</p>
            </div>
          ) : (
            <ScrollArea className="h-[300px] pr-4">
              <div className="grid grid-cols-2 gap-4">
                {screenshots.map((screenshot) => (
                  <div 
                    key={`${screenshot.step}-${screenshot.timestamp}`} 
                    className="border rounded-md p-2 overflow-hidden"
                  >
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-medium">Step {screenshot.step}</span>
                      <span className="text-xs text-muted-foreground">
                        {formatTimestamp(screenshot.timestamp)}
                      </span>
                    </div>
                    <div className="relative group">
                      <img 
                        src={screenshot.image} 
                        alt={`Screenshot from step ${screenshot.step}`}
                        className="w-full h-auto rounded-md object-cover cursor-pointer"
                        onClick={() => setSelectedScreenshot(screenshot)}
                      />
                      <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all flex items-center justify-center opacity-0 group-hover:opacity-100">
                        <Button 
                          variant="secondary" 
                          size="sm"
                          onClick={() => setSelectedScreenshot(screenshot)}
                        >
                          <Maximize2 className="h-4 w-4 mr-2" />
                          Expand
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>

      {/* Modal for expanded screenshot view */}
      {selectedScreenshot && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-background rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="p-4 border-b flex justify-between items-center">
              <h3 className="font-medium">
                Step {selectedScreenshot.step} - {formatTimestamp(selectedScreenshot.timestamp)}
              </h3>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setSelectedScreenshot(null)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="p-4 overflow-auto flex-1">
              <img 
                src={selectedScreenshot.image} 
                alt={`Screenshot from step ${selectedScreenshot.step}`}
                className="max-w-full h-auto mx-auto"
              />
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default ScreenshotDisplay;
