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
      <Sidebar activeItem={activeItem} />
      <MobileNavigation activeItem={activeItem} />
      <main className="app__main">
        <div className="app__content">{children}</div>
      </main>
    </div>
  );
}

export default AppLayout;