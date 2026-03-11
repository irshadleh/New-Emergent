import "@/App.css";
import { BrowserRouter, Routes, Route, useLocation, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { Toaster } from "./components/ui/sonner";
import Navbar from "./components/Navbar";
import PasswordChangeDialog from "./components/PasswordChangeDialog";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import AuthCallback from "./pages/AuthCallback";
import Apply from "./pages/Apply";
import Marketplace from "./pages/Marketplace";
import BikeDetail from "./pages/BikeDetail";
import CustomerDashboard from "./pages/CustomerDashboard";
import ShopDashboard from "./pages/ShopDashboard";
import TravelAgentDashboard from "./pages/TravelAgentDashboard";
import AdminDashboard from "./pages/AdminDashboard";
import About from "./pages/About";

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function AppRouter() {
  const location = useLocation();
  const { user, refreshUser } = useAuth();

  // Check URL fragment for session_id synchronously during render
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }

  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/apply" element={<Apply />} />
        <Route path="/marketplace" element={<Marketplace />} />
        <Route path="/bikes/:id" element={<BikeDetail />} />
        <Route path="/about" element={<About />} />
        <Route path="/dashboard" element={
          <ProtectedRoute><CustomerDashboard /></ProtectedRoute>
        } />
        <Route path="/shop" element={
          <ProtectedRoute><ShopDashboard /></ProtectedRoute>
        } />
        <Route path="/travel-agent" element={
          <ProtectedRoute><TravelAgentDashboard /></ProtectedRoute>
        } />
        <Route path="/admin" element={
          <ProtectedRoute><AdminDashboard /></ProtectedRoute>
        } />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>

      {/* Force password change dialog */}
      {user?.must_change_password && (
        <PasswordChangeDialog open={true} onComplete={refreshUser} />
      )}
    </>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRouter />
        <Toaster position="top-right" richColors />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;