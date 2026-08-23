import { Link, useNavigate } from "react-router-dom";
import LanguageSwitcher from "./LanguageSwitcher";
import BottomNav from "./BottomNav";
import { useApp } from "../context/AppContext";

export function Header({ dark = false, showBack = false }) {
  const navigate = useNavigate();
  const { t } = useApp();
  return (
    <header
      className={`sticky top-0 z-20 flex items-center justify-between px-4 py-3 sm:px-8 ${
        dark ? "bg-leaf-deep text-white" : "bg-husk/90 backdrop-blur"
      }`}
    >
      <div className="flex items-center gap-2">
        {showBack && (
          <button
            type="button"
            onClick={() => navigate(-1)}
            aria-label={t.back}
            className={`mr-1 flex h-8 w-8 items-center justify-center rounded-full text-lg ${
              dark ? "hover:bg-white/10" : "hover:bg-husk-deep"
            }`}
          >
            ←
          </button>
        )}
        <Link to="/" className="font-display text-xl font-semibold tracking-tight">
          {t.appName}
        </Link>
      </div>
      <LanguageSwitcher variant={dark ? "dark" : "light"} />
    </header>
  );
}

export default function PageShell({ children, dark = false, showBack = false }) {
  return (
    <div className="min-h-dvh bg-husk pb-16 sm:pb-0">
      <Header dark={dark} showBack={showBack} />
      <main>{children}</main>
      <BottomNav />
    </div>
  );
}
