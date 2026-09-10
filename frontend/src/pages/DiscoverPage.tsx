import DiscoveryBuilder from "../components/DiscoveryBuilder";
import RecentDiscoveries from "../components/RecentDiscoveries";

function DiscoverPage() {
  return (
    <section className="discover">
      <header className="discover__header">
        <h1 className="discover__title">Good evening.</h1>
        <p className="discover__subtitle">
          What do you want to discover today?
        </p>
        <p className="discover__support">
          Shape your discovery and let HarmonIQ find something that fits.
        </p>
      </header>

      <DiscoveryBuilder />

      <RecentDiscoveries />
    </section>
  );
}

export default DiscoverPage;