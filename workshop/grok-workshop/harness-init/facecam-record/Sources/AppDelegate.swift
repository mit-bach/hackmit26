import AppKit
import UserNotifications

final class AppDelegate: NSObject, NSApplicationDelegate {
    private let recorder = Recorder()
    private var statusItem: NSStatusItem?
    private var savingHUD: NSPanel?

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        buildStatusItem()
        recorder.onStateChange = { [weak self] state in
            self?.refreshUI(state)
        }
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound]) { _, _ in }

        // Dock / Finder launch starts a take immediately.
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) { [weak self] in
            self?.toggle()
        }
    }

    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        toggle()
        return false
    }

    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
        switch recorder.state {
        case .idle:
            return .terminateNow
        case .recording:
            recorder.stop { [weak self] err, url in
                self?.finishStop(error: err, url: url, thenQuit: true)
            }
            return .terminateLater
        case .saving:
            return .terminateLater
        }
    }

    @objc private func toggle() {
        switch recorder.state {
        case .idle:
            recorder.start { [weak self] err in
                if let err = err { self?.alert(err) }
            }
        case .recording:
            recorder.stop { [weak self] err, url in
                self?.finishStop(error: err, url: url, thenQuit: false)
            }
        case .saving:
            break
        }
    }

    @objc private func quit() {
        NSApp.terminate(nil)
    }

    @objc private func revealLast() {
        if let url = recorder.lastOutputURL {
            NSWorkspace.shared.activateFileViewerSelecting([url])
        }
    }

    private func finishStop(error: Error?, url: URL?, thenQuit: Bool) {
        if let error = error {
            alert(error)
        } else if let url = url {
            NSWorkspace.shared.activateFileViewerSelecting([url])
            notifySaved(url)
        }
        if thenQuit {
            NSApp.reply(toApplicationShouldTerminate: true)
        }
    }

    private func buildStatusItem() {
        let item = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        item.button?.image = NSImage(systemSymbolName: "record.circle", accessibilityDescription: "FaceCam Record")
        item.button?.imagePosition = .imageOnly
        let menu = NSMenu()
        menu.addItem(NSMenuItem(title: "Start / Stop Recording", action: #selector(toggle), keyEquivalent: "r"))
        menu.addItem(NSMenuItem(title: "Reveal Last Recording", action: #selector(revealLast), keyEquivalent: "o"))
        menu.addItem(.separator())
        menu.addItem(NSMenuItem(title: "Quit FaceCam Record", action: #selector(quit), keyEquivalent: "q"))
        item.menu = menu
        statusItem = item
    }

    private func refreshUI(_ state: Recorder.State) {
        switch state {
        case .idle:
            NSApp.dockTile.badgeLabel = nil
            statusItem?.button?.contentTintColor = nil
            statusItem?.button?.image = NSImage(systemSymbolName: "record.circle", accessibilityDescription: "FaceCam Record")
            hideHUD()
        case .recording:
            NSApp.dockTile.badgeLabel = "●"
            statusItem?.button?.contentTintColor = .systemRed
            statusItem?.button?.image = NSImage(systemSymbolName: "stop.circle.fill", accessibilityDescription: "Stop")
            hideHUD()
        case .saving:
            NSApp.dockTile.badgeLabel = "…"
            statusItem?.button?.contentTintColor = .systemOrange
            showHUD("Stitching face cam onto the screen…")
        }
        NSApp.dockTile.display()
    }

    private func showHUD(_ text: String) {
        if savingHUD == nil {
            let panel = NSPanel(
                contentRect: NSRect(x: 0, y: 0, width: 360, height: 56),
                styleMask: [.titled, .nonactivatingPanel],
                backing: .buffered,
                defer: false
            )
            panel.title = "FaceCam Record"
            panel.isFloatingPanel = true
            panel.level = .statusBar
            panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
            panel.sharingType = .none
            savingHUD = panel
        }
        let field = NSTextField(labelWithString: text)
        field.font = NSFont.systemFont(ofSize: 13, weight: .medium)
        field.alignment = .center
        field.frame = NSRect(x: 16, y: 16, width: 328, height: 24)
        savingHUD?.contentView?.subviews.forEach { $0.removeFromSuperview() }
        savingHUD?.contentView?.addSubview(field)
        if let screen = NSScreen.main {
            var f = savingHUD!.frame
            f.origin.x = screen.visibleFrame.midX - f.width / 2
            f.origin.y = screen.visibleFrame.midY - f.height / 2
            savingHUD?.setFrame(f, display: true)
        }
        savingHUD?.orderFrontRegardless()
    }

    private func hideHUD() {
        savingHUD?.orderOut(nil)
    }

    private func notifySaved(_ url: URL) {
        let content = UNMutableNotificationContent()
        content.title = "Recording saved"
        content.body = url.lastPathComponent
        let req = UNNotificationRequest(identifier: UUID().uuidString, content: content, trigger: nil)
        UNUserNotificationCenter.current().add(req, withCompletionHandler: nil)
    }

    private func alert(_ error: Error) {
        let a = NSAlert()
        a.alertStyle = .warning
        a.messageText = "FaceCam Record"
        a.informativeText = error.localizedDescription
        if let recErr = error as? RecorderError, case .screenDenied = recErr {
            a.addButton(withTitle: "Open Settings")
            a.addButton(withTitle: "OK")
            if a.runModal() == .alertFirstButtonReturn {
                Self.openScreenPrivacySettings()
            }
            return
        }
        a.runModal()
    }

    static func openScreenPrivacySettings() {
        let urls = [
            "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture",
            "x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension?Privacy_ScreenCapture"
        ]
        for s in urls {
            if let url = URL(string: s), NSWorkspace.shared.open(url) { return }
        }
    }
}
