/**
 * WTTJ Sync Service
 * Swipply registration ke saath WTTJ form automatically fill hota hai
 */

interface RegistrationData {
  email: string;
  password: string;
  firstName?: string;
  lastName?: string;
  role: 'candidate' | 'recruiter';
}

interface SyncResponse {
  success: boolean;
  message: string;
  session_id?: string;
  error?: string;
}

interface SyncStatus {
  status: 'started' | 'filling' | 'ready' | 'error';
  progress?: number;
  message?: string;
  error?: string;
}

const SYNC_SERVICE_URL = 'http://localhost:8012';

/**
 * Swipply registration ke saath WTTJ form fill karo
 */
export async function syncWTTJRegistration(data: RegistrationData): Promise<SyncResponse> {
  try {
    console.log('🔄 Starting WTTJ form sync for:', data.email);
    
    const response = await fetch(`${SYNC_SERVICE_URL}/api/sync-registration`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: data.email,
        password: data.password,
        first_name: data.firstName || 'User',
        last_name: data.lastName || 'Swipply',
        role: data.role,
      }),
    });

    const result = await response.json();
    
    if (result.success) {
      console.log('✅ WTTJ form filling started in background');
      
      // Show notification to user
      showNotification('WTTJ form is being filled automatically!', 'info');
    }
    
    return result;
    
  } catch (error) {
    console.error('❌ WTTJ sync error:', error);
    return {
      success: false,
      message: 'Failed to sync WTTJ form',
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Check karo WTTJ form filling ka status
 */
export async function checkSyncStatus(sessionId: string): Promise<SyncStatus> {
  try {
    const response = await fetch(`${SYNC_SERVICE_URL}/api/sync-status/${sessionId}`);
    const result = await response.json();
    
    if (result.success) {
      return result.status;
    } else {
      return {
        status: 'error',
        error: result.error || 'Status check failed',
      };
    }
  } catch (error) {
    return {
      status: 'error',
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Real-time updates via WebSocket
 */
export class WTTJSyncWebSocket {
  private ws: WebSocket | null = null;
  private onStatusUpdate: ((status: SyncStatus) => void) | null = null;
  
  connect() {
    this.ws = new WebSocket(`ws://localhost:8012/ws/registration-sync`);
    
    this.ws.onopen = () => {
      console.log('🔌 Connected to WTTJ sync service');
    };
    
    this.ws.onmessage = (event) => {
      const data: SyncStatus = JSON.parse(event.data);
      console.log('📨 WTTJ sync update:', data);
      
      if (this.onStatusUpdate) {
        this.onStatusUpdate(data);
      }
      
      // Show notifications based on status
      if (data.status === 'ready') {
        showNotification('✅ WTTJ form is ready to submit!', 'success');
      } else if (data.status === 'error') {
        showNotification('❌ WTTJ form filling failed', 'error');
      }
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    this.ws.onclose = () => {
      console.log('🔌 Disconnected from WTTJ sync service');
    };
  }
  
  sendRegistrationData(data: RegistrationData) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        action: 'register',
        data: {
          email: data.email,
          password: data.password,
          first_name: data.firstName || 'User',
          last_name: data.lastName || 'Swipply',
          role: data.role,
        },
      }));
    }
  }
  
  onUpdate(callback: (status: SyncStatus) => void) {
    this.onStatusUpdate = callback;
  }
  
  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

/**
 * Helper function to show notifications
 */
function showNotification(message: string, type: 'info' | 'success' | 'error') {
  // You can integrate with your toast/notification system
  console.log(`[${type.toUpperCase()}] ${message}`);
  
  // Example: Using browser notification API
  if ('Notification' in window && Notification.permission === 'granted') {
    new Notification('WTTJ Sync', {
      body: message,
      icon: '/wttj-icon.png',
    });
  }
}

/**
 * Request notification permission
 */
export async function requestNotificationPermission() {
  if ('Notification' in window && Notification.permission === 'default') {
    await Notification.requestPermission();
  }
}
