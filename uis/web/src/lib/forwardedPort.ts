// Codespaces serves each forwarded port at `<name>-<port>.app.github.dev`, so
// another port is reached by swapping the port in the current host.
export function forwardedPortUrl(port: number): string {
  if (typeof window === "undefined") return `http://localhost:${port}`;
  const codespace = window.location.hostname.match(/^(.+)-\d+(\.[\w.-]*app\.github\.dev)$/);
  if (codespace) return `${window.location.protocol}//${codespace[1]}-${port}${codespace[2]}`;
  return `http://localhost:${port}`;
}
