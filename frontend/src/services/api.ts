import { API_BASE } from '../config';
import { getAuth } from 'firebase/auth';

export interface AnonymousSession {
  session_id: string;
  uploaded_photo_url?: string;
  analysis_results?: any;
  storage_path?: string;
  generated_images?: {
      goal: string;
      url: string;
      path: string;
  }[];
}

export const anonymousApi = {
  uploadPhoto: async (file: File, sessionId?: string | null): Promise<AnonymousSession> => {
    const formData = new FormData();
    formData.append('file', file);
    if (sessionId) {
      formData.append('session_id', sessionId);
    }

    const response = await fetch(`${API_BASE}/anonymous/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Upload failed');
    }

    return response.json();
  },

  analyzePhoto: async (sessionId: string): Promise<any> => {
    const response = await fetch(`${API_BASE}/anonymous/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ session_id: sessionId }),
    });

    if (!response.ok) {
      throw new Error('Analysis failed');
    }

    return response.json();
  },

  getResults: async (sessionId: string): Promise<AnonymousSession> => {
    const response = await fetch(`${API_BASE}/anonymous/results/${sessionId}`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch results');
    }

    return response.json();
  },

  generateTransformations: async (sessionId: string, goal: string): Promise<any> => {
    const response = await fetch(`${API_BASE}/anonymous/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ session_id: sessionId, goal }),
    });

    if (!response.ok) {
      throw new Error('Generation failed');
    }

    return response.json();
  },

  migrateData: async (sessionId: string, token: string): Promise<void> => {
    const response = await fetch(`${API_BASE}/anonymous/migrate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ session_id: sessionId }),
    });

    if (!response.ok) {
      throw new Error('Migration failed');
    }
  },

  suggestPath: async (sessionId: string): Promise<any> => {
    const response = await fetch(`${API_BASE}/anonymous/suggest`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ session_id: sessionId }),
    });

    if (!response.ok) {
      throw new Error('Failed to get suggestion');
    }

    return response.json();
  },

  generatePlan: async (goal: string): Promise<any> => {
    const response = await fetch(`${API_BASE}/anonymous/plan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ goal }),
    });

    if (!response.ok) {
      throw new Error('Failed to generate plan');
    }

    return response.json();
  }
};

export const observeApi = {
  getScan: async (scanId: string): Promise<any> => {
    const auth = getAuth();
    const user = auth.currentUser;
    if (!user) {
        throw new Error('User not authenticated');
    }
    const token = await user.getIdToken();
    
    const response = await fetch(`${API_BASE}/observe/scans/${scanId}`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    if (!response.ok) {
        throw new Error('Failed to fetch scan');
    }
    
    return response.json();
  }
};

export const decideApi = {
  suggestPath: async (): Promise<any> => {
    const auth = getAuth();
    const user = auth.currentUser;
    if (!user) {
        throw new Error('User not authenticated');
    }
    const token = await user.getIdToken();
    
    const response = await fetch(`${API_BASE}/decide/suggest`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    if (!response.ok) {
        throw new Error('Failed to get suggestion');
    }
    
    return response.json();
  }
};

export const actApi = {
  generatePlan: async (forceRefresh: boolean = false, goal?: string): Promise<any> => {
    const auth = getAuth();
    const user = auth.currentUser;
    if (!user) throw new Error('User not authenticated');
    const token = await user.getIdToken();

    const response = await fetch(`${API_BASE}/act/generate-plan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ force_refresh: forceRefresh, goal })
    });

    if (!response.ok) throw new Error('Failed to generate plan');
    return response.json();
  },

  chatWithAgent: async (message: string, dayId: string, currentPlan?: any): Promise<any> => {
    const auth = getAuth();
    const user = auth.currentUser;
    if (!user) throw new Error('User not authenticated');
    const token = await user.getIdToken();

    const response = await fetch(`${API_BASE}/act/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ message, day_id: dayId, current_plan: currentPlan })
    });

    if (!response.ok) throw new Error('Chat failed');
    return response.json();
  }
};
