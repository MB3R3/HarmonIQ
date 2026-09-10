import AppLayout from "./layouts/AppLayout";
import DiscoverPage from "./pages/DiscoverPage";

function App() {
  return (
    <AppLayout activeItem="discover">
      <DiscoverPage />
    </AppLayout>
  );
}

export default App;