/**
 * Joins classnames, filtering out falsy values (`undefined`, `null`,
 * `false`, `''`). A single shared helper so every primitive composes
 * conditional classnames the same way (STORY-120).
 */
export function cx(
  ...parts: Array<string | undefined | null | false>
): string {
  return parts.filter(Boolean).join(' ')
}
