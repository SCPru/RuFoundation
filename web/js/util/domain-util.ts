export function getDomainName(hostname: string): string {
  return hostname.split(".").slice(-2).join(".");
}


export function isInternalLink(prop: URL | null): boolean {
  if (!prop) return false;
  
  return getDomainName(prop.hostname) === getDomainName(window.location.hostname);
}
