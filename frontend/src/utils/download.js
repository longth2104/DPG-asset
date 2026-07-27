// Blobs come back from axios (Bearer-authenticated) rather than a bare <a href>,
// since the PDF/export endpoints require auth and a plain link can't send it.
export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

export function openBlobInNewTab(blob) {
  const url = URL.createObjectURL(blob)
  window.open(url, '_blank')
  // Revoke lazily — the new tab needs the URL to still be valid once it loads.
  setTimeout(() => URL.revokeObjectURL(url), 60_000)
}
