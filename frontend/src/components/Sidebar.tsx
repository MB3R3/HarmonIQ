import type { ReactNode } from "react";

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
  return (
    <aside className="sidebar">
      <div className="sidebar__brand">HarmonIQ</div>

      <nav className="sidebar__nav" aria-label="Main">
        <ul className="sidebar__list">
          {PRIMARY_ITEMS.map((item) => (
            <li key={item.key}>
              <a
                href="#"
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
            <a href="#" className="sidebar__link">
              <UserIcon />
              <span>Profile</span>
            </a>
          </li>
        </ul>
      </nav>

      <div className="sidebar__footer">
        <a href="#" className="sidebar__user">
          <span className="sidebar__avatar">
            <UserIcon />
          </span>
          <span className="sidebar__user-label">Your Profile</span>
        </a>
      </div>
    </aside>
  );
}

export default Sidebar;