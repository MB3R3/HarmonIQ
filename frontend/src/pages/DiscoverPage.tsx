import { useState } from "react";

import DiscoveryBuilder from "../components/DiscoveryBuilder";
import RecentDiscoveries from "../components/RecentDiscoveries";
import RecommendationPreview from "../components/RecommendationPreview";
import type { DiscoveryForm } from "../types/discovery";

const INITIAL_FORM: DiscoveryForm = {
  mood: null,
  genre: null,
  era: null,
  artist: "",
  discoveryStyle: "balanced",
};

function DiscoverPage() {
  const [form, setForm] = useState<DiscoveryForm>(INITIAL_FORM);
  const [request, setRequest] = useState<DiscoveryForm | null>(null);

  const handleSubmit = (next: DiscoveryForm) => {
    setRequest(next);
    console.log("Discovery request (frontend prototype, no API):", {
      mood: next.mood,
      genre: next.genre,
      era: next.era,
      artist: next.artist.trim() || null,
      discovery_style: next.discoveryStyle,
    });
  };

  return (
    <section className="discover">
      <header className="discover__header">
        <p className="eyebrow">Discover</p>
        <h1 className="discover__title">Good evening.</h1>
        <p className="discover__subtitle">
          What are you in the mood to hear?
        </p>
        <p className="discover__support">
          Shape a discovery and HarmonIQ will find something that fits.
        </p>
      </header>

      <DiscoveryBuilder form={form} onChange={setForm} onSubmit={handleSubmit} />

      <RecommendationPreview request={request} />

      <RecentDiscoveries />
    </section>
  );
}

export default DiscoverPage;