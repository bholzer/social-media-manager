import { api } from './api';

interface AuthResponse {
  access_token: string;
  token_type: string;
}

interface User {
  id: string;
  email: string;
  full_name: string | null;
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const data = await api.post<AuthResponse>('/auth/login', { email, password });
  localStorage.setItem('token', data.access_token);
  return data;
}

export async function register(email: string, password: string): Promise<AuthResponse> {
  const data = await api.post<AuthResponse>('/auth/register', {
    email,
    password,
  });
  localStorage.setItem('token', data.access_token);
  return data;
}

export function logout() {
  localStorage.removeItem('token');
}

export function getToken(): string | null {
  return localStorage.getItem('token');
}

export function isAuthenticated(): boolean {
  return getToken() !== null;
}
