// Model scores are deliberately not inputs to presentation labels.
export function relevanceLabel(primary) {
  if (!primary) return 'No recommendation available';
  return primary.is_mock ? 'Demo recommendation · Unverified' : 'Recommended · Unverified';
}
