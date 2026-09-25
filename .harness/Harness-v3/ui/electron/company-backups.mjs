/** Browser shim. Company backup transfer runs only in the desktop shell. */
export class CompanyBackupError extends Error {
  constructor(code, message) {
    super(message);
    this.name = "CompanyBackupError";
    this.code = code;
  }
}

export function createCompanyBackups() {
  return {
    backup() {
      return Promise.reject(new CompanyBackupError("unavailable", "Company backups need the desktop app."));
    },
    prepareRestore() {
      return Promise.reject(new CompanyBackupError("unavailable", "Company backups need the desktop app."));
    },
  };
}
