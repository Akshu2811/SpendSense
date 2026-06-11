import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './context/AuthContext';
import { isAuthenticated } from './services/api';

// Pages — lazy loaded to keep initial bundle small
const Landing = React.lazy(() => import('./pages/Landing'));
const Register = React.lazy(() => import('./pages/Register'));
const Login = React.lazy(() => import('./pages/Login'));
const OnboardingBudget = React.lazy(() => import('./pages/OnboardingBudget'));
const OnboardingConnect = React.lazy(() => import('./pages/OnboardingConnect'));
const OnboardingSuccess = React.lazy(() => import('./pages/OnboardingSuccess'));
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const AddPurchase = React.lazy(() => import('./pages/AddPurchase'));
const ShopCheck = React.lazy(() => import('./pages/ShopCheck'));
const Nudge = React.lazy(() => import('./pages/Nudge'));
const Report = React.lazy(() => import('./pages/Report'));
const Settings = React.lazy(() => import('./pages/Settings'));
const Privacy = React.lazy(() => import('./pages/Privacy'));
const Terms = React.lazy(() => import('./pages/Terms'));

function ProtectedRoute({ children }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function PageSuspense({ children }) {
  return (
    <React.Suspense
      fallback={
        <div className="flex items-center justify-center min-h-screen">
          <div className="shimmer-card w-full max-w-sm h-64 mx-4" />
        </div>
      }
    >
      {children}
    </React.Suspense>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <PageSuspense>
          <Routes>
            {/* Public */}
            <Route path="/" element={<Landing />} />
            <Route path="/register" element={<Register />} />
            <Route path="/login" element={<Login />} />
            <Route path="/privacy" element={<Privacy />} />
            <Route path="/terms" element={<Terms />} />

            {/* Onboarding (auth required) */}
            <Route
              path="/onboarding/budget"
              element={<ProtectedRoute><OnboardingBudget /></ProtectedRoute>}
            />
            <Route
              path="/onboarding/connect"
              element={<ProtectedRoute><OnboardingConnect /></ProtectedRoute>}
            />
            <Route
              path="/onboarding/success"
              element={<ProtectedRoute><OnboardingSuccess /></ProtectedRoute>}
            />

            {/* App (auth required) */}
            <Route
              path="/dashboard"
              element={<ProtectedRoute><Dashboard /></ProtectedRoute>}
            />
            <Route
              path="/add-purchase"
              element={<ProtectedRoute><AddPurchase /></ProtectedRoute>}
            />
            <Route
              path="/check-before-buy"
              element={<ProtectedRoute><ShopCheck /></ProtectedRoute>}
            />
            <Route
              path="/nudge"
              element={<ProtectedRoute><Nudge /></ProtectedRoute>}
            />
            <Route
              path="/report"
              element={<ProtectedRoute><Report /></ProtectedRoute>}
            />
            <Route
              path="/settings"
              element={<ProtectedRoute><Settings /></ProtectedRoute>}
            />

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </PageSuspense>
      </BrowserRouter>

      <Toaster
        position="top-center"
        toastOptions={{
          duration: 3500,
          style: {
            background: 'rgba(255,255,255,0.08)',
            backdropFilter: 'blur(12px)',
            WebkitBackdropFilter: 'blur(12px)',
            border: '0.5px solid rgba(255,255,255,0.14)',
            borderRadius: '12px',
            color: '#FFFFFF',
            fontFamily: "'DM Sans', system-ui, sans-serif",
            fontSize: '13px',
            padding: '12px 16px',
          },
          success: {
            iconTheme: { primary: '#4ECCA3', secondary: '#050D1A' },
          },
          error: {
            iconTheme: { primary: '#E63946', secondary: '#FFFFFF' },
          },
        }}
      />
    </AuthProvider>
  );
}
