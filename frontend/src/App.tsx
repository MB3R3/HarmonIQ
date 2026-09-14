import { useCallback, useEffect, useState } from "react";

import AppLayout from "./layouts/AppLayout";
import DiscoverPage from "./pages/DiscoverPage";
import LibraryPage from "./pages/LibraryPage";
import PreferencesPage from "./pages/PreferencesPage";

type Page = "discover" | "library" | "preferences";

function getPageFromHash(): Page {
  const hash = window.location.hash.replace(/^#\/?/, "");
  if (hash === "library") return "library";
  if (hash === "preferences") return "preferences";
  return "discover";
}

function App() {
  const [page, setPage] = useState<Page>(getPageFromHash);

  useEffect(() => {
    function onHashChange() {
      setPage(getPageFromHash());
    }
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  const handleNavigate = useCallback((target: string) => {
    window.location.hash = `#/${target}`;
  }, []);

  return (
    <AppLayout activeItem={page}>
      {page === "library" ? (
        <LibraryPage onNavigate={handleNavigate} />
      ) : page === "preferences" ? (
        <PreferencesPage />
      ) : (
        <DiscoverPage />
      )}
    </AppLayout>
  );
}

export default App;