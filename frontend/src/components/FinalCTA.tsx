import { useAuth } from "../context/useAuth";

function FinalCTA() {
  const { isAuthenticated } = useAuth();

  return (
    <section className="final-cta section">
      <div className="container final-cta__inner">
        <h2 className="final-cta__headline">
          Your next favorite song starts with a direction.
        </h2>
        <a
          href={isAuthenticated ? "#/discover" : "#/signup"}
          className="button button--primary button--large"
        >
          {isAuthenticated ? "Discover music" : "Get started"}
        </a>
      </div>
    </section>
  );
}

export default FinalCTA;