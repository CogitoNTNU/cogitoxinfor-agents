type QueryParams = {
    query: string;
    testing?: boolean;
    test_actions?: Array<[string, any]>;
    human_intervention?: boolean;
    config?: Record<string, any>;
  };
  
  type SessionResponse = {
    session_id: string;
    status: string;
  };
  
  type SessionStatusResponse = {
    status: string;
    result?: any;
  };
  
  const API_BASE_URL = 'http://localhost:8000/api';
  
  export const sendQuery = async (params: QueryParams): Promise<SessionResponse> => {
    const response = await fetch(`${API_BASE_URL}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    return response.json();
  };
  
  export const checkSessionStatus = async (sessionId: string): Promise<SessionStatusResponse> => {
    const response = await fetch(`${API_BASE_URL}/session/${sessionId}/status`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    return response.json();
  };
  
  export const triggerSessionProcessing = async (): Promise<any> => {
    const response = await fetch(`${API_BASE_URL}/session/process`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    return response.json();
  };