
class WebSocketService {
  socket: WebSocket | null = null;
  sessionId: string | null = null;
  messageListeners: ((data: any) => void)[] = [];
  
  connect(sessionId: string): Promise<boolean> {
    return new Promise((resolve) => {
      this.sessionId = sessionId;
      this.socket = new WebSocket(`ws://localhost:8000/api/ws/${sessionId}`);
      
      this.socket.onopen = () => {
        console.log('WebSocket connected');
        resolve(true);
      };
      
      this.socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.messageListeners.forEach(listener => listener(data));
      };
      
      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        resolve(false);
      };
      
      this.socket.onclose = () => {
        console.log('WebSocket connection closed');
      };
    });
  }
  
  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }
  
  sendMessage(message: any) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected');
    }
  }
  
  onMessage(callback: (data: any) => void) {
    this.messageListeners.push(callback);
    return () => {
      this.messageListeners = this.messageListeners.filter(listener => listener !== callback);
    };
  }
  
  respondToInterrupt(input: string) {
    this.sendMessage({
      type: 'INTERRUPT_RESPONSE',
      session_id: this.sessionId,
      input
    });
  }
}

export const websocketService = new WebSocketService();
