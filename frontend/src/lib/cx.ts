/**
 * Joins classnames, filtering out falsy values (`undefined`, `null`,
 * `false`, `''`). Replaces the `[...].filter(Boolean).join(' ')` idiom that
 * was duplicated across the shell primitives (STORY-041 AC2).
 */
export function cx(
  ...parts: Array<string | undefined | null | false>
): string {
  return parts.filter(Boolean).join(' ')
}
