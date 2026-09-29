const sections = [
  ["Research", "Run source-backed technical research with an observable agent workflow."],
  ["Knowledge", "Turn useful research into reusable engineering knowledge."],
  ["Capabilities", "Track what you can actually build, debug and explain."],
  ["Agent Lab", "Inspect runs, models, tools, events, latency and evaluation."],
];

export default function HomePage() {
  return (
    <main className="shell">
      <section className="hero">
        <p className="eyebrow">Personal AI Engineering Workspace</p>
        <h1>Build better engineering habits with observable AI agents.</h1>
        <p className="lead">
          V0.1 focuses on one complete research loop: task → agent → sources → report →
          knowledge → evaluation.
        </p>
      </section>

      <section className="grid">
        {sections.map(([title, description]) => (
          <article className="card" key={title}>
            <h2>{title}</h2>
            <p>{description}</p>
          </article>
        ))}
      </section>

      <section className="status">
        <span className="dot" aria-hidden="true" />
        <span>MVP architecture foundation in progress</span>
      </section>
    </main>
  );
}
