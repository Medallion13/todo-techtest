import { useState } from 'react';
import { useAuth } from './contexts/AuthContext';
import { LoginForm } from './components/auth/LoginForm';
import { RegisterForm } from './components/auth/RegisterForm';

function App() {
  const { isAuthenticated, email, logout } = useAuth();
  const [showRegister, setShowRegister] = useState(false);

  if (isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-100 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white shadow-md rounded px-8 py-6 mb-4">
            <div className="flex justify-between items-center">
              <h1 className="text-2xl font-bold">Welcome, {email}!</h1>
              <button
                onClick={logout}
                className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
              >
                Logout
              </button>
            </div>
          </div>
          <div className="text-center text-gray-600 mt-8">
            Task list coming next...
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 py-12 px-4">
      <div className="max-w-md mx-auto">
        <h1 className="text-4xl font-bold text-center mb-8">Todo App</h1>
        
        {showRegister ? <RegisterForm /> : <LoginForm />}
        
        <div className="text-center mt-4">
          <button
            onClick={() => setShowRegister(!showRegister)}
            className="text-blue-500 hover:text-blue-700"
          >
            {showRegister ? 'Already have an account? Login' : "Don't have an account? Register"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;