/** Browser shim. The desktop enrollment bridge is absent outside Electron. */
export function managedPortalOrigin(value) {
  return new URL(value).origin;
}
