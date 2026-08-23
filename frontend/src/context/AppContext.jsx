import { createContext, useContext, useMemo, useState } from "react";
import { STRINGS } from "../i18n/strings";

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [language, setLanguage] = useState("en");
  const [location, setLocation] = useState(null); // {lat, lng, state, district}

  const t = useMemo(() => STRINGS[language] ?? STRINGS.en, [language]);

  const value = { language, setLanguage, location, setLocation, t };
  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used within AppProvider");
  return ctx;
}
