import { useCallback, useEffect, useState } from "react";

import AppLayout from "./layouts/AppLayout";
import ProtectedRoute from "./components/ProtectedRoute";
import DiscoverPage from "./pages/DiscoverPage";
import LibraryPage from "./pages/LibraryPage";
import LoginPage from "./pages/LoginPage";
import PreferencesPage from "./pages/PreferencesPage";
import ProfilePage from "./pages/ProfilePage";
import SignUpPage from "./pages/SignUpPage";

type Page = "discover" | "library" | "preferences" | "profile";

function pageFromHash(): Page {
  const hash = window.location.hash.replace(/^#\/?/, "");
  if (hash === "library") return "library";
  if (hash === "preferences") return "preferences";
  if (hash === "profile") return "profile";
  return "discover";
}

function isLoginRoute(): boolean {
  return window.location.hash.replace(/^#\/?/, "") === "login";
}

function isSignupRoute(): boolean {
  return window.location.hash.replace(/^#\/?/, "") === "signup";
}

function App() {
  const [page, setPage] = useState<Page>(pageFromHash);
  const [showLogin, setShowLogin] = useState<boolean>(isLoginRoute);
  const [showSignup, setShowSignup] = useState<boolean>(isSignupRoute);

  useEffect(() => {
    function onHashChange() {
      setPage(pageFromHash());
      setShowLogin(isLoginRoute());
      setShowSignup(isSignupRoute());
    }
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  const handleNavigate = useCallback((target: string) => {
    window.location.hash = `#/${target}`;
  }, []);

  if (showLogin) {
    return <LoginPage />;
  }

  if (showSignup) {
    return <SignUpPage />;
  }

  return (
    <ProtectedRoute>
      <AppLayout activeItem={page}>
        {page === "library" ? (
          <LibraryPage onNavigate={handleNavigate} />
        ) : page === "preferences" ? (
          <PreferencesPage />
        ) : page === "profile" ? (
          <ProfilePage />
        ) : (
          <DiscoverPage />
        )}
      </AppLayout>
    </ProtectedRoute>
  );
}

export default App;