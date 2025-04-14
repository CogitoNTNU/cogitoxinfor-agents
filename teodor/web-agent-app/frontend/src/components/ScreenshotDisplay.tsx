
import React from 'react';
import { Card, CardContent } from './ui/card';
import { Loader } from 'lucide-react';

interface ScreenshotDisplayProps {
  imageUrl: string | null;
  step: number;
  loading?: boolean;
}

export const ScreenshotDisplay: React.FC<ScreenshotDisplayProps> = ({ 
  imageUrl, 
  step,
  loading = false 
}) => {
  return (
    <Card className="border overflow-hidden">
      <CardContent className="p-0 relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/80 z-10">
            <Loader className="h-10 w-10 animate-spin text-primary" />
          </div>
        )}
        
        {imageUrl ? (
          <div className="relative">
            <img 
              src={imageUrl} 
              alt={`Screenshot from step ${step}`}
              className="w-full h-auto object-contain"
            />
            <div className="absolute top-2 right-2 bg-primary text-primary-foreground text-xs py-1 px-2 rounded">
              Step {step}
            </div>
          </div>
        ) : (
          <div className="h-64 flex items-center justify-center text-muted-foreground">
            {loading ? "Loading screenshot..." : "No screenshot available"}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
