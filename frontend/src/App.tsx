import { lazy, Suspense } from 'react';
import { createBrowserRouter, Navigate, RouterProvider, useLocation, type RouteObject } from 'react-router-dom';
import { MotionConfig } from 'framer-motion';
import Layout from './components/layout/Layout';
import Home from './pages/Home';
import About from './pages/About';
import Pricing from './pages/Pricing';
import Contact from './pages/Contact';
import Privacy from './pages/Privacy';
import Terms from './pages/Terms';
import NotFound from './pages/NotFound';
import YourData from './pages/YourData';
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import { PageLoader } from './components/common/Spinner';
import { ToastProvider } from './components/common/Toaster';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import { getConfig } from './config/runtime';

const TopicExplorer = lazy(() => import('./pages/topics/TopicExplorer'));
const TopicWorkspace = lazy(() => import('./pages/topics/TopicWorkspace'));
const MyTests = lazy(() => import('./pages/topics/MyTests'));
const VerifyEmail = lazy(() => import('./pages/auth/VerifyEmail'));
const ForgotPassword = lazy(() => import('./pages/auth/ForgotPassword'));
const ResetPassword = lazy(() => import('./pages/auth/ResetPassword'));
const LegacyChat = lazy(() => import('./pages/legacy/LegacyChat'));
const LegacyTests = lazy(() => import('./pages/legacy/LegacyTests'));

function Protected({ children }: { children: React.ReactNode }) {
  const { status } = useAuth();
  const location = useLocation();
  if (status === 'loading') return <PageLoader />;
  if (status === 'anonymous') return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />;
  return <Suspense fallback={<PageLoader />}>{children}</Suspense>;
}

const lazyPage = (el: React.ReactNode) => <Suspense fallback={<PageLoader />}>{el}</Suspense>;

export function buildRoutes(mode = getConfig().apiMode): RouteObject[] {
  const v1 = mode === 'v1';
  return [
    {
      element: <Layout />,
      children: [
        { path: '/', element: <Home /> },
        { path: '/about', element: <About /> },
        { path: '/pricing', element: <Pricing /> },
        { path: '/contact', element: <Contact /> },
        { path: '/privacy', element: <Privacy /> },
        { path: '/terms', element: <Terms /> },
        { path: '/data', element: <YourData /> },
        { path: '/login', element: <Login /> },
        { path: '/register', element: <Register /> },
        ...(v1
          ? [
              { path: '/verify-email', element: lazyPage(<VerifyEmail />) },
              { path: '/forgot-password', element: lazyPage(<ForgotPassword />) },
              { path: '/reset-password', element: lazyPage(<ResetPassword />) },
              { path: '/topics', element: <Protected><TopicExplorer /></Protected> },
              { path: '/topics/:topicId/*', element: <Protected><TopicWorkspace /></Protected> },
              { path: '/tests', element: <Protected><MyTests /></Protected> },
              // The single-document chat is replaced by topics (TOP-12).
              { path: '/chat', element: <Navigate to="/topics" replace /> },
            ]
          : [
              { path: '/chat', element: <Protected><LegacyChat /></Protected> },
              { path: '/tests', element: <Protected><LegacyTests /></Protected> },
              { path: '/topics/*', element: <Navigate to="/chat" replace /> },
            ]),
        { path: '*', element: <NotFound /> },
      ],
    },
  ];
}

const router = createBrowserRouter(buildRoutes());

function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <ToastProvider>
          {/* Honour the OS "reduce motion" setting for every framer-motion animation. */}
          <MotionConfig reducedMotion="user">
            <RouterProvider router={router} />
          </MotionConfig>
        </ToastProvider>
      </ThemeProvider>
    </AuthProvider>
  );
}

export default App;
