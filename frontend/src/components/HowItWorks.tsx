type Step = {
  number: string;
  title: string;
  description: string;
};

const STEPS: Step[] = [
  {
    number: "01",
    title: "Choose",
    description:
      "Tell HarmonIQ what kind of music you're looking for.",
  },
  {
    number: "02",
    title: "Discover",
    description:
      "Get recommendations based on your preferences.",
  },
  {
    number: "03",
    title: "Refine",
    description:
      "Like, skip, save, and shape future discoveries.",
  },
];

function HowItWorks() {
  return (
    <section id="how-it-works" className="how section">
      <div className="container">
        <div className="how__heading">
          <p className="eyebrow">How it works</p>
          <h2>Three steps to your next favorite song.</h2>
        </div>

        <ol className="how__steps">
          {STEPS.map((step) => (
            <li className="how__step" key={step.number}>
              <span className="how__number">{step.number}</span>
              <h3 className="how__title">{step.title}</h3>
              <p className="how__copy">{step.description}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

export default HowItWorks;