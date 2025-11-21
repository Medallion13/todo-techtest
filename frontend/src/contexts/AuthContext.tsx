import {
  createContext,
  useContext,
  useState,
  useEffect,
  type ReactNode,
} from "react";
import { API_CONFIG, apiRequest } from "../config/api";

interface AuthContextType {
  token: string | null;
  email: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setToken] = useState<string | null>(null);
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    const savedToken = localStorage.getItem("token");
    const savedEmail = localStorage.getItem("email");
    if (savedToken) {
      setToken(savedToken);
      setEmail(savedEmail);
    }
  }, []);

  const register = async (email: string, password: string) => {
    const response = await apiRequest(API_CONFIG.ENDPOINTS.REGISTER, {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });

    if (response.statusCode !== 201) {
      throw new Error(response.body?.message || "Registration failed");
    }
  };

  const login = async (email: string, password: string) => {
    const response = await apiRequest(API_CONFIG.ENDPOINTS.LOGIN, {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });

    if (response.statusCode !== 200) {
      throw new Error(response.body?.message || "Login failed");
    }

    const { idToken } = response.body;

    // Guardar token y email
    localStorage.setItem("token", idToken);
    localStorage.setItem("email", email);
    setToken(idToken);
    setEmail(email);
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("email");
    setToken(null);
    setEmail(null);
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        email,
        login,
        register,
        logout,
        isAuthenticated: !!token,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};
