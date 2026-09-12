// Model scores are deliberately not inputs to presentation labels.
export function relevanceLabel(primary) {
  if (!primary) return 'No recommendation available';
  return 'Recommended Standard';
}
