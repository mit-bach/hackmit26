import AppKit
import AVFoundation
import QuartzCore

/// Always-on-top face-cam window that rides above fullscreen apps and is
/// excluded from screen capture (`sharingType = .none`). The recorded PIP is
/// stitched on later from a separate camera file.
final class OverlayPanel: NSPanel {
    let pipSize: CGFloat = 220
    private let margin: CGFloat = 18
    private let preview = PreviewView()
    private let recDot = NSView()

    override var canBecomeKey: Bool { false }
    override var canBecomeMain: Bool { false }

    init() {
        let rect = NSRect(x: 0, y: 0, width: pipSize, height: pipSize)
        super.init(
            contentRect: rect,
            styleMask: [.borderless, .nonactivatingPanel],
            backing: .buffered,
            defer: false
        )
        isFloatingPanel = true
        becomesKeyOnlyIfNeeded = true
        hidesOnDeactivate = false
        isOpaque = false
        backgroundColor = .clear
        hasShadow = true
        isMovableByWindowBackground = true
        animationBehavior = .none
        collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary, .ignoresCycle]
        sharingType = .none
        level = NSWindow.Level(rawValue: Int(CGWindowLevelForKey(.assistiveTechHighWindow)))
        ignoresMouseEvents = false
        isExcludedFromWindowsMenu = true

        guard let content = contentView else { return }
        content.wantsLayer = true
        content.layer?.backgroundColor = NSColor.black.cgColor
        content.layer?.cornerRadius = 22
        content.layer?.masksToBounds = true
        content.layer?.borderWidth = 3
        content.layer?.borderColor = NSColor.white.withAlphaComponent(0.92).cgColor

        preview.frame = content.bounds
        preview.autoresizingMask = [.width, .height]
        content.addSubview(preview)

        recDot.wantsLayer = true
        recDot.layer?.backgroundColor = NSColor.systemRed.cgColor
        recDot.layer?.cornerRadius = 6
        recDot.frame = NSRect(x: 12, y: content.bounds.height - 24, width: 12, height: 12)
        recDot.autoresizingMask = [.minYMargin, .maxXMargin]
        content.addSubview(recDot)
    }

    func attach(session: AVCaptureSession) {
        preview.previewLayer.session = session
        preview.previewLayer.videoGravity = .resizeAspectFill
    }

    func placeDefault(on screen: NSScreen) {
        if let saved = UserDefaults.standard.string(forKey: "pipFrame") {
            let f = NSRectFromString(saved)
            if screen.frame.intersects(f) {
                setFrame(f, display: true)
                return
            }
        }
        let vf = screen.visibleFrame
        let x = vf.maxX - pipSize - margin
        let y = vf.minY + margin
        setFrame(NSRect(x: x, y: y, width: pipSize, height: pipSize), display: true)
    }

    func persistFrame() {
        UserDefaults.standard.set(NSStringFromRect(frame), forKey: "pipFrame")
    }
}

final class PreviewView: NSView {
    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        wantsLayer = true
    }

    required init?(coder: NSCoder) {
        super.init(coder: coder)
        wantsLayer = true
    }

    override func makeBackingLayer() -> CALayer {
        AVCaptureVideoPreviewLayer()
    }

    var previewLayer: AVCaptureVideoPreviewLayer {
        return layer as! AVCaptureVideoPreviewLayer
    }
}
