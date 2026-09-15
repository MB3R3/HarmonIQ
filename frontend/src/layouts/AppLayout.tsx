import type { ReactNode } from "react";

import MobileNavigation from "../components/MobileNavigation";
import Sidebar from "../components/Sidebar";

type AppLayoutProps = {
  activeItem?: string;
  children: ReactNode;
};

function AppLayout({ activeItem = "discover", children }: AppLayoutProps) {
  return (
    <div className="app">
      <a href="#main-content" className="skip-link">
        Skip to content
      </a>
      <Sidebar activeItem={activeItem} />
      <MobileNavigation activeItem={activeItem} />
      <main className="app__main" id="main-content" tabIndex={-1}>
        <div className="app__content">{children}</div>
      </main>
    </div>
  );
}

export default AppLayout;