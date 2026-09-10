import { useState } from "react";

import DiscoveryBuilder from "../components/DiscoveryBuilder";
import RecentDiscoveries from "../components/RecentDiscoveries";
import RecommendationResults from "../components/RecommendationResults";
import { discoverMusic } from "../services/recommendations";
import type { DiscoveryForm } from "../types/discovery";
import type { Recommendation } from "../types/recommendation";

const INITIAL_FORM: DiscoveryForm = {
  mood: null,
  genre: null,
  era: null,
  artist: "",
  discoveryStyle: "balanced",
};

function DiscoverPage() {
  const [form, setForm] = useState<DiscoveryForm>(INITIAL_FORM);
  const [submittedForm, setSubmittedForm] =
    useState<DiscoveryForm>(INITIAL_FORM);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<Recommendation[]>([]);
  const [hasSubmitted, setHasSubmitted] = useState(false);

  const handleSubmit = async (next: DiscoveryForm) => {
    setError(null);
    setIsLoading(true);
    setHasSubmitted(true);

    try {
      const response = await discoverMusic(next);
      setResults(response.results);
      setSubmittedForm(next);
    } catch (err) {
      setResults([]);
      setError(
        err instanceof Error
          ? err.message
          : "Unable to discover music right now. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
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

      <RecommendationResults
        form={submittedForm}
        hasSubmitted={hasSubmitted}
        isLoading={isLoading}
        error={error}
        results={results}
        onRetry={() => handleSubmit(form)}
      />

      <RecentDiscoveries />
    </section>
  );
}

export default DiscoverPage;