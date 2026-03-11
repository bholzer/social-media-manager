import { createBrowserRouter, Navigate } from 'react-router';
import { isAuthenticated } from '@/lib/auth';
import AppLayout from '@/layouts/AppLayout';
import LoginPage from '@/pages/LoginPage';
import RegisterPage from '@/pages/RegisterPage';
import DashboardPage from '@/pages/DashboardPage';
import PostsPage from '@/pages/PostsPage';
import AccountsPage from '@/pages/AccountsPage';
import FacebookOAuthCallbackPage from '@/pages/FacebookOAuthCallbackPage';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function GuestRoute({ children }: { children: React.ReactNode }) {
  if (isAuthenticated()) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
}

export const router = createBrowserRouter([
  {
    path: '/login',
    element: (
      <GuestRoute>
        <LoginPage />
      </GuestRoute>
    ),
  },
  {
    path: '/register',
    element: (
      <GuestRoute>
        <RegisterPage />
      </GuestRoute>
    ),
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'posts', element: <PostsPage /> },
      { path: 'accounts', element: <AccountsPage /> },
      { path: 'accounts/facebook/callback', element: <FacebookOAuthCallbackPage /> },
    ],
  },
]);
