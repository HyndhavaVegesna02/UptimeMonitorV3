import './StyleguidePage.css'

/**
 * The design-system gallery (STORY-120 AC6) — renders every primitive in
 * every state so the visual language can be reviewed and reused in one
 * place. Primitive sections are filled in as each one lands (step 5); this
 * is the bootstrap shell that makes the route reachable.
 */
export function StyleguidePage() {
  return (
    <div className="styleguide">
      <h1>Design system</h1>
      <p className="styleguide__intro">
        Every primitive, in every state — the single source of truth for the
        Uptime Monitor visual language.
      </p>
    </div>
  )
}
