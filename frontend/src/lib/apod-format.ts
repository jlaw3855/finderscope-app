const SKY_SURPRISE_PATTERN = /\s*Sky Surprise:.*$/is

/** Remove APOD's promotional Sky Surprise footer (requires external link integration). */
export function formatApodExplanation(explanation: string): string {
  return explanation.replace(SKY_SURPRISE_PATTERN, '').trim()
}
