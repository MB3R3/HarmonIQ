import Navbar from "../components/Navbar";
import Hero from "../components/Hero";
import DiscoveryPreview from "../components/DiscoveryPreview";
import HowItWorks from "../components/HowItWorks";
import FinalCTA from "../components/FinalCTA";

function LandingPage() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
      </main>
      <DiscoveryPreview />
      <HowItWorks />
      <FinalCTA />
    </>
  );
}

export default LandingPage;