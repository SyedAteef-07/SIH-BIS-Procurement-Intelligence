// Hide repeated service boilerplate while retaining analysis facts and scope.
// Never apply this to identifiers, tender wording, or extracted requirements.
export function presentationText(value) {
  if (typeof value !== 'string') return '';
  return value
    .replace(/Fictional fixture scope:\s*/gi, 'Scope: ')
    .split(/(?<=[.!?])\s+/)
    .filter(sentence => !/^(?:Demo\b|Fictional\b|Contains fictional\b|These are not official\b|Scores are uncalibrated\b|Relevance scores are uncalibrated\b|Reliability filtering is disabled\b|Metadata validity\b|Status and revision are dataset metadata\b|Based on fictional\b|This is not a compliance verdict\b|A mention is not proof\b|Coverage describes topic mentions only\b|Verify current BIS\/QCO\b)/i.test(sentence.trim()))
    .join(' ')
    .trim();
}

export function statusLabel(value) {
  const status = typeof value === 'string' && value.trim() ? value.trim() : 'unverified';
  return status.charAt(0).toUpperCase() + status.slice(1);
}
