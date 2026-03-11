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
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);

  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? 'Login failed');
  }

  const data: AuthResponse = await response.json();
  localStorage.setItem('token', data.access_token);
  return data;
}

export async function register(email: string, password: string, fullName?: string): Promise<User> {
  return api.post<User>('/auth/register', {
    email,
    password,
    full_name: fullName,
  });
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
