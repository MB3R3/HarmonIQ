import { useCallback, useEffect, useState } from "react";

import AppLayout from "./layouts/AppLayout";
import DiscoverPage from "./pages/DiscoverPage";
import LibraryPage from "./pages/LibraryPage";

type Page = "discover" | "library";

function getPageFromHash(): Page {
  const hash = window.location.hash.replace(/^#\/?/, "");
  if (hash === "library") return "library";
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
      ) : (
        <DiscoverPage />
      )}
    </AppLayout>
  );
}

export default App;