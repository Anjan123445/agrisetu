import { useState, useRef, useEffect } from "react";
import { LANGUAGES } from "../i18n/strings";
import { useApp } from "../context/AppContext";

export default function LanguageSwitcher({ variant = "light" }) {
  const { language, setLanguage } = useApp();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const current = LANGUAGES.find((l) => l.code === language) ?? LANGUAGES[0];

  useEffect(() => {
    function onClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const isDark = variant === "dark";

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
        className={`flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-semibold transition-colors ${
          isDark
            ? "border-white/30 text-white hover:bg-white/10"
            : "border-ink/15 text-ink hover:bg-husk-deep"
        }`}
      >
        <span aria-hidden="true">🌐</span>
        {current.native}
      </button>
      {open && (
        <ul
          role="listbox"
          className="absolute right-0 z-20 mt-2 w-40 overflow-hidden rounded-xl border border-ink/10 bg-white shadow-lg"
        >
          {LANGUAGES.map((lang) => (
            <li key={lang.code}>
              <button
                type="button"
                role="option"
                aria-selected={lang.code === language}
                onClick={() => {
                  setLanguage(lang.code);
                  setOpen(false);
                }}
                className={`flex w-full items-center justify-between px-4 py-2.5 text-left text-sm hover:bg-husk ${
                  lang.code === language ? "font-bold text-leaf" : "text-ink"
                }`}
              >
                <span>{lang.native}</span>
                {lang.code === language && <span aria-hidden="true">✓</span>}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
