import React, { useState, useEffect } from 'react'; // Import useState and useEffect from react
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselPrevious,
  CarouselNext,
} from './ui/carousel'; // Remove useCarousel import here
import { Trash2, Maximize2, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';
// Removed useAgent import


export interface Screenshot {
  id: string;
  url: string;
  // Assuming step and timestamp might not be directly available in SSE data
  // If needed, they would need to be added in Index.tsx before passing
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
  loading // loading is now a prop
}) => {
  // Removed useAgent hook usage
  const [selectedScreenshot, setSelectedScreenshot] = useState<Screenshot | null>(null);
  const [api, setApi] = useState<any>(); // State to hold the carousel API

  useEffect(() => {
    if (api && screenshots.length > 0) {
      // Ensure carousel re-initializes when new items arrive
      api.reInit();
      // Scroll to the newest screenshot
      api.scrollTo(screenshots.length - 1);
    }
  }, [api, screenshots]);

  return (
    <>
      <Card className={cn("w-full border-none", className)}>
          {screenshots.length === 0 && loading ? ( // Use loading prop
              <div className="flex items-center justify-center flex-1 border border-dashed rounded-md">
                <p className="text-muted-foreground">Agent waiting for task...</p> {/* Or a loading indicator */}
              </div>
          ) : screenshots.length === 0 ? (
            <div className="flex items-center justify-center flex-1 border border-dashed rounded-md">
              <p className="text-muted-foreground">No screenshots available</p>
            </div>
          ) : (
            <div className="relative flex-1 overflow-visible">
              <Carousel className="h-full w-full" setApi={setApi}> {/* Pass setApi to Carousel */}
                <CarouselPrevious
                  className="absolute left-2 top-1/2 -translate-y-1/2 bg-background/50 hover:bg-background z-10"
                />
                <CarouselContent className="h-full">
                  {screenshots.map((screenshot) => (
                    <CarouselItem key={screenshot.id}>
                      <div className="border rounded-md p-2 overflow-hidden">
                        <div className="flex justify-between items-center mb-2">
                          <span className="font-medium">Screenshot {screenshots.indexOf(screenshot) + 1}</span>
                        </div>
                        <div className="relative group">
                          <img
                            src={screenshot.url}
                            alt={`Screenshot ${screenshots.indexOf(screenshot) + 1}`}
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
                    </CarouselItem>
                  ))}
                </CarouselContent>
                <CarouselNext
                  className="absolute right-2 top-1/2 -translate-y-1/2 bg-background/50 hover:bg-background z-10"
                />
              </Carousel>
            </div>
          )}
      </Card>

      {/* Modal for expanded screenshot view */}
      {selectedScreenshot && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-background rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="p-4 border-b flex justify-between items-center">
              <h3 className="font-medium">
                Screenshot {screenshots.indexOf(selectedScreenshot) + 1} {/* Display index in modal */}
                {/* Timestamp might not be available */}
                {/* - {formatTimestamp(selectedScreenshot.timestamp)} */}
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
                src={selectedScreenshot.url} // Use url property
                alt={`Screenshot ${screenshots.indexOf(selectedScreenshot) + 1}`} // Use index for alt text
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
