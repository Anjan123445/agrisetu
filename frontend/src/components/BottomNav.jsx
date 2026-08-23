import { NavLink } from "react-router-dom";
import { useApp } from "../context/AppContext";

const ITEMS = [
  { to: "/", icon: "⌂", key: "navHome" },
  { to: "/advisory", icon: "🌾", key: "navAdvisory" },
  { to: "/diagnose", icon: "🍃", key: "navDisease" },
  { to: "/ask", icon: "🎙", key: "navVoice" },
  { to: "/network", icon: "📊", key: "navCoop" },
];

export default function BottomNav() {
  const { t } = useApp();
  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-30 border-t border-ink/10 bg-white/95 backdrop-blur sm:hidden"
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
      aria-label="Primary"
    >
      <ul className="flex justify-between px-1">
        {ITEMS.map((item) => (
          <li key={item.to} className="flex-1">
            <NavLink
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `flex flex-col items-center gap-0.5 py-2 text-[11px] font-semibold ${
                  isActive ? "text-leaf" : "text-ink/50"
                }`
              }
            >
              <span className="text-lg" aria-hidden="true">
                {item.icon}
              </span>
              {t[item.key]}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
