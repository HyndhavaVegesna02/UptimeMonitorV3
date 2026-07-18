import './SampleModeChip.css'

export interface SampleModeChipProps {
  /** Restores the dismissed `SampleModeBanner` — `AppShell` passes its
   * `useDismissibleBanner().restore`. */
  onRestore: () => void
}

/**
 * Persistent "SAMPLE" chip (STORY-104 AC3, ported from `ui-redesign`
 * STORY-102 AC2 — salvage list): shown once the banner has been dismissed
 * while the flag is still ON, so the operator always has SOME indicator
 * beyond the switch's own accent. Click restores the banner.
 */
export function SampleModeChip({ onRestore }: SampleModeChipProps) {
  return (
    <button
      type="button"
      className="sample-mode-chip"
      onClick={onRestore}
      aria-label="Sample mode is on — signals recorded as DOWN. Click to show details."
    >
      SAMPLE
    </button>
  )
}
