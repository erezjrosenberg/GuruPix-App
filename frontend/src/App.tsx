import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { ProfileProvider } from "@/contexts/ProfileContext";
import LoginPage from "@/pages/LoginPage";
import GoogleCallbackPage from "@/pages/GoogleCallbackPage";
import HomePage from "@/pages/HomePage";
import OnboardingPage from "@/pages/OnboardingPage";
import CatalogPage from "@/pages/CatalogPage";

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ProfileProvider>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/onboarding" element={<OnboardingPage />} />
            <Route path="/catalog" element={<CatalogPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/auth/google/callback"
              element={<GoogleCallbackPage />}
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </ProfileProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
