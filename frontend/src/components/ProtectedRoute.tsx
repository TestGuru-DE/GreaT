// REQ-4001: ProtectedRoute - Wendet alle untergeordneten Routes nur fuer authentifizierte User
// REQ-4028 AK-1: Route-Guard: Bei passwordChangeRequired=true auf /account/password umleiten
import { useEffect, useState } from "react";
import { useAuthStore } from "../store/authStore";
import { useNavigate, Outlet, useLocation } from "react-router-dom";

export default function ProtectedRoute() {
  const user = useAuthStore((s) => s.user);
  const passwordChangeRequired = useAuthStore((s) => s.passwordChangeRequired);
  const loadUser = useAuthStore((s) => s.loadUser);
  const navigate = useNavigate();
  const location = useLocation();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    async function checkAuth() {
      await loadUser();
      setIsChecking(false);
    }
    checkAuth();
  }, [loadUser]);

  useEffect(() => {
    if (!isChecking && !user) {
      navigate("/login");
    }
  }, [user, isChecking, navigate]);

  // REQ-4028 AK-1: Wenn password_change_required, auf /account/password umleiten
  // Ausser wenn der User bereits auf /account/password ist
  useEffect(() => {
    if (!isChecking && user && passwordChangeRequired && location.pathname !== "/account/password") {
      navigate("/account/password");
    }
  }, [user, passwordChangeRequired, isChecking, location.pathname, navigate]);

  if (isChecking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-theme-bg">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return user ? <Outlet /> : null;
}