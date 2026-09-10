import type { ReactNode } from "react";

import {
  DiscoverIcon,
  LibraryIcon,
  PreferencesIcon,
  UserIcon,
} from "./icons";

type MobileItem = {
  key: string;
  label: string;
  icon: ReactNode;
};

type MobileNavigationProps = {
  activeItem?: string;
};

const MOBILE_ITEMS: MobileItem[] = [
  { key: "discover", label: "Discover", icon: <DiscoverIcon /> },
  { key: "library", label: "Library", icon: <LibraryIcon /> },
  { key: "preferences", label: "Preferences", icon: <PreferencesIcon /> },
  { key: "profile", label: "Profile", icon: <UserIcon /> },
];

function MobileNavigation({ activeItem = "discover" }: MobileNavigationProps) {
  return (
    <nav className="mobile-nav" aria-label="Mobile">
      {MOBILE_ITEMS.map((item) => (
        <a
          key={item.key}
          href="#"
          className={`mobile-nav__link${item.key === activeItem ? " mobile-nav__link--active" : ""}`}
          aria-current={item.key === activeItem ? "page" : undefined}
        >
          {item.icon}
          <span>{item.label}</span>
        </a>
      ))}
    </nav>
  );
}

export default MobileNavigation;