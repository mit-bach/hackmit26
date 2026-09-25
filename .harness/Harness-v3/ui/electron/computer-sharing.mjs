/** Browser shim. Folder sharing is a desktop-main concern. */
export async function validateSharedFolders() {
  return [];
}

export function createComputerSharing() {
  return {
    state() {
      return { enabled: false, folders: [], terminal: false, computer: false };
    },
  };
}
