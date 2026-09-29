import Link from "next/link";

const sections = [
  {
    title: "Research",
    description: "Run source-backed technical research with an observable agent workflow.",
    href: "/research",
    status: "Available",
  },
  {
    title: "Knowledge",
    description: "Turn useful research into reusable engineering knowledge.",
    href: null,
    status: "Next",
  },
  {
    title: "Capabilities",
    description: "Track what you can actually build, debug and explain.",
    href: null,
    status: "Planned",
  },
  {
    title: "Agent Lab",
    description: "Inspect runs, models, tools, events, latency and evaluation.",
    href: null,
    status: "Planned",
  },
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
        <div className="hero-actions">
          <Link className="primary-link" href="/research">
            Open Research Workspace
          </Link>
        </div>
      </section>

      <section className="grid">
        {sections.map((section) => {
          const content = (
            <>
              <div className="card-heading">
                <h2>{section.title}</h2>
                <span className="mini-status">{section.status}</span>
              </div>
              <p>{section.description}</p>
            </>
          );

          return section.href ? (
            <Link className="card card-link" href={section.href} key={section.title}>
              {content}
            </Link>
          ) : (
            <article className="card" key={section.title}>
              {content}
            </article>
          );
        })}
      </section>

      <section className="status">
        <span className="dot" aria-hidden="true" />
        <span>Research Loop implementation active</span>
      </section>
    </main>
  );
}
