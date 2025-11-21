export const API_CONFIG = {
  BASE_URL: 'https://65czwklzp5.execute-api.us-east-1.amazonaws.com/prod',
  ENDPOINTS: {
    REGISTER: '/auth/register',
    LOGIN: '/auth/login',
    TASKS: '/tasks',
  },
};

// Helper para hacer requests con token
export const apiRequest = async (
  endpoint: string,
  options: RequestInit = {}
): Promise<any> => {
  const token = localStorage.getItem('token');
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_CONFIG.BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  const data = await response.json();
  
  // API Gateway devuelve {statusCode, body}
  if (data.body && typeof data.body === 'string') {
    return {
      ...data,
      body: JSON.parse(data.body),
    };
  }
  
  return data;
};