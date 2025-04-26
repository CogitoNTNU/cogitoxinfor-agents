
import React from 'react';
import { AgentEvent } from '../context/AgentContext';
import { Cpu, MessageSquare, Image, AlertTriangle, CheckCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';

interface EventTimelineProps {
  events: AgentEvent[];
}

export const EventTimeline: React.FC<EventTimelineProps> = ({ events }) => {
  if (events.length === 0) {
    return (
      <div className="text-center text-muted-foreground p-4">
        No events to display yet
      </div>
    );
  }

  return (
    <div className="space-y-4 p-4">
      {events.map((event) => (
        <Card key={event.id} className="border-l-4 border-l-primary">
          <CardHeader className="p-3 pb-0">
            <CardTitle className="text-sm flex items-center gap-2">
              {event.type === 'ACTION_UPDATE' && (
                <>
                  <Cpu size={16} className="text-agent-action" />
                  <span>Action: {event.payload.action}</span>
                </>
              )}
              {event.type === 'SCREENSHOT_UPDATE' && (
                <>
                  <Image size={16} className="text-primary" />
                  <span>Screenshot</span>
                </>
              )}
              {event.type === 'INTERRUPT' && (
                <>
                  <AlertTriangle size={16} className="text-agent-interrupt" />
                  <span>Interrupt</span>
                </>
              )}
              {event.type === 'FINAL_ANSWER' && (
                <>
                  <CheckCircle size={16} className="text-agent-answer" />
                  <span>Final Answer</span>
                </>
              )}
              <span className="ml-auto text-xs text-muted-foreground">
                {event.timestamp.toLocaleTimeString()}
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-3 text-sm">
            {event.type === 'ACTION_UPDATE' && (
              <div>
                <div className="font-semibold">{event.payload.action}</div>
                <div className="text-muted-foreground">{JSON.stringify(event.payload.args)}</div>
              </div>
            )}
            {event.type === 'SCREENSHOT_UPDATE' && (
              <div className="text-xs text-muted-foreground">
                Step: {event.payload.step}
              </div>
            )}
            {event.type === 'INTERRUPT' && (
              <div>{event.payload.message}</div>
            )}
            {event.type === 'FINAL_ANSWER' && (
              <div>{event.payload.answer}</div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
};
