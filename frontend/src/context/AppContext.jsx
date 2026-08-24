import { createContext, useContext, useMemo, useState, useEffect } from "react";
import { STRINGS } from "../i18n/strings";

// Generate and persist a stable device ID
export function getOrCreateDeviceId() {
  let id = localStorage.getItem("agrisetu_device_id");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("agrisetu_device_id", id);
  }
  return id;
}

const AppContext = createContext(null);

function loadInitialLanguage() {
  return localStorage.getItem("agrisetu_language") || "en";
}
function loadInitialLocation() {
  try {
    const raw = localStorage.getItem("agrisetu_location");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function AppProvider({ children }) {
  const [language, setLanguageState] = useState(loadInitialLanguage);
  const [location, setLocationState] = useState(loadInitialLocation); // {lat, lng, state, district}
  const [deviceId, setDeviceId] = useState(null);

  // Initialize on mount to safely access localStorage
  useEffect(() => {
    setDeviceId(getOrCreateDeviceId());
  }, []);

  const setLanguage = (lang) => {
    setLanguageState(lang);
    localStorage.setItem("agrisetu_language", lang);
  };
  const setLocation = (loc) => {
    setLocationState(loc);
    localStorage.setItem("agrisetu_location", JSON.stringify(loc));
  };

  const t = useMemo(() => STRINGS[language] ?? STRINGS.en, [language]);

  const value = { language, setLanguage, location, setLocation, t, deviceId };
  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used within AppProvider");
  return ctx;
}