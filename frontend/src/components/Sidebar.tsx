import { useState } from "react";
import type { ReactNode } from "react";

import { useAuth } from "../context/useAuth";
import {
  ClockIcon,
  DiscoverIcon,
  LibraryIcon,
  PreferencesIcon,
  UserIcon,
} from "./icons";

type NavItem = {
  key: string;
  label: string;
  icon: ReactNode;
};

type SidebarProps = {
  activeItem?: string;
};

const PRIMARY_ITEMS: NavItem[] = [
  { key: "discover", label: "Discover", icon: <DiscoverIcon /> },
  { key: "library", label: "Library", icon: <LibraryIcon /> },
  { key: "preferences", label: "Preferences", icon: <PreferencesIcon /> },
  { key: "recent", label: "Recent Listens", icon: <ClockIcon /> },
];

function Sidebar({ activeItem = "discover" }: SidebarProps) {
  const { user, logout } = useAuth();
  const [isSigningOut, setIsSigningOut] = useState(false);

  const displayName = user?.username || "Your Profile";
  const avatarInitial = user ? user.username.charAt(0).toUpperCase() : null;

  const handleSignOut = async () => {
    setIsSigningOut(true);
    try {
      await logout();
    } finally {
      setIsSigningOut(false);
    }
  };

  return (
    <aside className="sidebar">
      <div className="sidebar__brand">HarmonIQ</div>

      <nav className="sidebar__nav" aria-label="Main">
        <ul className="sidebar__list">
          {PRIMARY_ITEMS.map((item) => (
            <li key={item.key}>
              <a
                href={`#/${item.key}`}
                className={`sidebar__link${item.key === activeItem ? " sidebar__link--active" : ""}`}
                aria-current={
                  item.key === activeItem ? "page" : undefined
                }
              >
                {item.icon}
                <span>{item.label}</span>
              </a>
            </li>
          ))}
        </ul>

        <div className="sidebar__separator" role="separator" />

        <ul className="sidebar__list">
          <li>
            <a
              href="#/profile"
              className={`sidebar__link${activeItem === "profile" ? " sidebar__link--active" : ""}`}
              aria-current={activeItem === "profile" ? "page" : undefined}
            >
              <UserIcon />
              <span>Profile</span>
            </a>
          </li>
        </ul>
      </nav>

      <div className="sidebar__footer">
        <div className="sidebar__user">
          <span className="sidebar__avatar">
            {avatarInitial ? <span>{avatarInitial}</span> : <UserIcon />}
          </span>
          <span className="sidebar__user-label">{displayName}</span>
        </div>
        <button
          type="button"
          className="sidebar__signout"
          onClick={handleSignOut}
          disabled={isSigningOut}
        >
          {isSigningOut ? "Signing out…" : "Sign out"}
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;