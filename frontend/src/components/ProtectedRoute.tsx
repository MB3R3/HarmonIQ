import type { ReactNode } from "react";

import LandingPage from "../pages/LandingPage";
import AppLoading from "./AppLoading";
import { useAuth } from "../context/useAuth";

type ProtectedRouteProps = {
  children: ReactNode;
};

function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { status } = useAuth();

  if (status === "loading") {
    return <AppLoading />;
  }

  if (status === "unauthenticated") {
    return <LandingPage />;
  }

  return <>{children}</>;
}

export default ProtectedRoute;