import AppKit
import AVFoundation
import CoreGraphics
import Foundation

enum RecorderError: LocalizedError {
    case noCamera
    case cameraDenied
    case screenDenied
    case alreadyBusy
    case captureFailed(String)

    var errorDescription: String? {
        switch self {
        case .noCamera: return "No camera is available."
        case .cameraDenied: return "Camera access was denied. Enable it in System Settings → Privacy & Security → Camera."
        case .screenDenied: return "Screen Recording is off for FaceCam Record. Enable it in System Settings → Privacy & Security → Screen Recording, then click the Dock icon again. The face cam is recorded separately and stitched on after you stop, so it still appears over fullscreen."
        case .alreadyBusy: return "Already recording or saving."
        case .captureFailed(let s): return s
        }
    }
}

final class Recorder: NSObject, AVCaptureFileOutputRecordingDelegate {
    enum State {
        case idle
        case recording
        case saving
    }

    private(set) var state: State = .idle
    var onStateChange: ((State) -> Void)?
    var lastOutputURL: URL?

    private let session = AVCaptureSession()
    private let movieOutput = AVCaptureMovieFileOutput()
    private var screenProcess: Process?
    private var caffeineProcess: Process?
    private var camFinish: ((Error?) -> Void)?
    private var workDir: URL?
    private var screenURL: URL?
    private var camURL: URL?

    let overlay = OverlayPanel()

    func prepareSession() throws {
        if session.inputs.isEmpty {
            session.beginConfiguration()
            session.sessionPreset = .hd1280x720
            guard let cam = AVCaptureDevice.default(for: .video) else {
                session.commitConfiguration()
                throw RecorderError.noCamera
            }
            let input = try AVCaptureDeviceInput(device: cam)
            if session.canAddInput(input) { session.addInput(input) }
            if session.canAddOutput(movieOutput) { session.addOutput(movieOutput) }
            if let audio = movieOutput.connection(with: .audio) {
                audio.isEnabled = false
            }
            session.commitConfiguration()
        }
        overlay.attach(session: session)
        if !session.isRunning {
            session.startRunning()
        }
    }

    func start(completion: @escaping (Error?) -> Void) {
        guard state == .idle else {
            completion(RecorderError.alreadyBusy)
            return
        }

        AVCaptureDevice.requestAccess(for: .video) { [weak self] camOK in
            guard let self = self else { return }
            if !camOK {
                DispatchQueue.main.async { completion(RecorderError.cameraDenied) }
                return
            }
            AVCaptureDevice.requestAccess(for: .audio) { _ in
                DispatchQueue.main.async {
                    if !CGPreflightScreenCaptureAccess() {
                        _ = CGRequestScreenCaptureAccess()
                    }
                    if !CGPreflightScreenCaptureAccess() {
                        completion(RecorderError.screenDenied)
                        return
                    }
                    do {
                        try self.prepareSession()
                        try self.beginCapture()
                        completion(nil)
                    } catch {
                        completion(error)
                    }
                }
            }
        }
    }

    private func beginCapture() throws {
        guard let ffmpeg = Self.ffmpegPath() else {
            throw RecorderError.captureFailed("ffmpeg not found at /opt/homebrew/bin/ffmpeg.")
        }
        let devices = Self.avfoundationDevices(ffmpeg: ffmpeg)
        let stamp = Self.timestamp()
        let dir = URL(fileURLWithPath: NSTemporaryDirectory())
            .appendingPathComponent("FaceCamRecord-\(stamp)", isDirectory: true)
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        workDir = dir
        screenURL = dir.appendingPathComponent("screen.mov")
        camURL = dir.appendingPathComponent("cam.mov")
        let logURL = dir.appendingPathComponent("screen.log")

        let screen = NSScreen.main ?? NSScreen.screens[0]
        overlay.placeDefault(on: screen)
        overlay.orderFrontRegardless()

        movieOutput.startRecording(to: camURL!, recordingDelegate: self)

        FileManager.default.createFile(atPath: logURL.path, contents: nil)
        let logHandle = try FileHandle(forWritingTo: logURL)

        let sc = Process()
        sc.executableURL = URL(fileURLWithPath: ffmpeg)
        sc.arguments = [
            "-nostdin", "-hide_banner", "-y",
            "-f", "avfoundation",
            "-capture_cursor", "1",
            "-framerate", "30",
            "-i", "\(devices.screen):\(devices.mic)",
            "-c:v", "h264_videotoolbox",
            "-b:v", "12M",
            "-c:a", "aac",
            "-b:a", "160k",
            screenURL!.path
        ]
        sc.standardOutput = logHandle
        sc.standardError = logHandle
        try sc.run()
        screenProcess = sc

        let caf = Process()
        caf.executableURL = URL(fileURLWithPath: "/usr/bin/caffeinate")
        caf.arguments = ["-dimsu", "-w", String(sc.processIdentifier)]
        try? caf.run()
        caffeineProcess = caf

        Thread.sleep(forTimeInterval: 0.6)
        if !sc.isRunning {
            let log = (try? String(contentsOf: logURL)) ?? ""
            overlay.orderOut(nil)
            if movieOutput.isRecording { movieOutput.stopRecording() }
            throw RecorderError.captureFailed("Screen capture exited immediately. \(log.suffix(500))")
        }

        state = .recording
        onStateChange?(.recording)
    }

    func stop(completion: @escaping (Error?, URL?) -> Void) {
        guard state == .recording else {
            completion(RecorderError.captureFailed("Not recording."), nil)
            return
        }
        state = .saving
        onStateChange?(.saving)
        overlay.persistFrame()

        let group = DispatchGroup()
        var camError: Error?

        group.enter()
        camFinish = { err in
            camError = err
            group.leave()
        }
        if movieOutput.isRecording {
            movieOutput.stopRecording()
        } else {
            camFinish?(nil)
            camFinish = nil
        }

        if let sc = screenProcess, sc.isRunning {
            sc.interrupt()
        }

        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            guard let self = self else { return }
            self.screenProcess?.waitUntilExit()
            self.caffeineProcess?.terminate()
            let waitCam = group.wait(timeout: .now() + 12)
            if waitCam == .timedOut {
                camError = RecorderError.captureFailed("Camera file did not finish writing.")
            }

            DispatchQueue.main.async {
                self.overlay.orderOut(nil)
            }

            if let err = camError {
                DispatchQueue.main.async {
                    self.resetToIdle()
                    completion(err, nil)
                }
                return
            }

            do {
                let out = try self.composite()
                self.lastOutputURL = out
                DispatchQueue.main.async {
                    self.resetToIdle()
                    completion(nil, out)
                }
            } catch {
                DispatchQueue.main.async {
                    self.resetToIdle()
                    completion(error, nil)
                }
            }
        }
    }

    private func resetToIdle() {
        screenProcess = nil
        caffeineProcess = nil
        camFinish = nil
        state = .idle
        onStateChange?(.idle)
    }

    func fileOutput(
        _ output: AVCaptureFileOutput,
        didFinishRecordingTo outputFileURL: URL,
        from connections: [AVCaptureConnection],
        error: Error?
    ) {
        let finish = camFinish
        camFinish = nil
        finish?(error)
    }

    private func composite() throws -> URL {
        guard let screenURL = screenURL, let camURL = camURL else {
            throw RecorderError.captureFailed("Missing capture files.")
        }
        let fm = FileManager.default
        var waited = 0
        while !fm.fileExists(atPath: screenURL.path) && waited < 50 {
            Thread.sleep(forTimeInterval: 0.1)
            waited += 1
        }
        guard fm.fileExists(atPath: screenURL.path) else {
            throw RecorderError.captureFailed("Screen recording did not save. Grant Screen Recording to FaceCam Record in System Settings → Privacy & Security.")
        }
        guard fm.fileExists(atPath: camURL.path) else {
            throw RecorderError.captureFailed("Camera recording did not save.")
        }

        let videoSize = Self.probeSize(screenURL) ?? Self.fallbackVideoSize()
        let pip = pipRect(inVideo: videoSize)
        let ffmpeg = Self.ffmpegPath()
        let stamp = Self.timestamp()
        let desktop = FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("Desktop")
        let outURL = desktop.appendingPathComponent("Screen-Facecam-Mic_\(stamp).mov")

        guard let ffmpeg = ffmpeg else {
            let raw = desktop.appendingPathComponent("Screen-Mic_\(stamp).mov")
            try fm.copyItem(at: screenURL, to: raw)
            let rawCam = desktop.appendingPathComponent("FaceCam_\(stamp).mov")
            try fm.copyItem(at: camURL, to: rawCam)
            throw RecorderError.captureFailed("ffmpeg not found. Saved the two raw files to Desktop instead of stitching.")
        }

        let w = max(2, Int(pip.width.rounded()) / 2 * 2)
        let h = max(2, Int(pip.height.rounded()) / 2 * 2)
        let x = max(0, Int(pip.origin.x.rounded()))
        let y = max(0, Int(pip.origin.y.rounded()))
        let border = 6
        let filter = "[1:v]fps=30,scale=\(w):\(h):force_original_aspect_ratio=increase,crop=\(w):\(h),pad=\(w + border * 2):\(h + border * 2):\(border):\(border):white[cam];[0:v][cam]overlay=\(x):\(y):eof_action=repeat[v]"

        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: ffmpeg)
        proc.arguments = [
            "-y",
            "-i", screenURL.path,
            "-i", camURL.path,
            "-filter_complex", filter,
            "-map", "[v]",
            "-map", "0:a?",
            "-c:v", "h264_videotoolbox",
            "-b:v", "12M",
            "-c:a", "aac",
            "-b:a", "160k",
            "-movflags", "+faststart",
            outURL.path
        ]
        let errPipe = Pipe()
        proc.standardOutput = FileHandle.nullDevice
        proc.standardError = errPipe
        try proc.run()
        proc.waitUntilExit()
        if proc.terminationStatus != 0 {
            let errData = errPipe.fileHandleForReading.readDataToEndOfFile()
            let msg = String(data: errData, encoding: .utf8) ?? "ffmpeg failed"
            let raw = desktop.appendingPathComponent("Screen-Mic_\(stamp).mov")
            try? fm.copyItem(at: screenURL, to: raw)
            throw RecorderError.captureFailed("Stitch failed (\(proc.terminationStatus)). Screen file saved. \(msg.suffix(400))")
        }
        try? fm.removeItem(at: workDir!)
        workDir = nil
        return outURL
    }

    /// Map the live overlay frame (AppKit, bottom-left) onto ffmpeg overlay
    /// coordinates (top-left, in the recorded pixel buffer).
    private func pipRect(inVideo videoSize: CGSize) -> CGRect {
        let screen = NSScreen.main ?? NSScreen.screens[0]
        let sf = screen.frame
        let wf = overlay.frame
        let nx = (wf.minX - sf.minX) / sf.width
        let nyTop = (sf.maxY - wf.maxY) / sf.height
        let nw = wf.width / sf.width
        let nh = wf.height / sf.height
        var r = CGRect(
            x: nx * videoSize.width,
            y: nyTop * videoSize.height,
            width: nw * videoSize.width,
            height: nh * videoSize.height
        )
        if r.maxX > videoSize.width { r.origin.x = videoSize.width - r.width }
        if r.maxY > videoSize.height { r.origin.y = videoSize.height - r.height }
        r.origin.x = max(0, r.origin.x)
        r.origin.y = max(0, r.origin.y)
        return r
    }

    private static func probeSize(_ url: URL) -> CGSize? {
        guard let probe = ffmpegSibling("ffprobe") else { return nil }
        let p = Process()
        p.executableURL = URL(fileURLWithPath: probe)
        p.arguments = [
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0:s=x",
            url.path
        ]
        let out = Pipe()
        p.standardOutput = out
        p.standardError = FileHandle.nullDevice
        do { try p.run() } catch { return nil }
        p.waitUntilExit()
        let data = out.fileHandleForReading.readDataToEndOfFile()
        let s = String(data: data, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        let parts = s.split(separator: "x")
        guard parts.count == 2,
              let w = Double(parts[0]),
              let h = Double(parts[1]),
              w > 0, h > 0 else { return nil }
        return CGSize(width: w, height: h)
    }

    private static func fallbackVideoSize() -> CGSize {
        let s = NSScreen.main ?? NSScreen.screens[0]
        let scale = s.backingScaleFactor
        return CGSize(width: s.frame.width * scale, height: s.frame.height * scale)
    }

    private static func avfoundationDevices(ffmpeg: String) -> (screen: Int, mic: Int) {
        let p = Process()
        p.executableURL = URL(fileURLWithPath: ffmpeg)
        p.arguments = ["-hide_banner", "-f", "avfoundation", "-list_devices", "true", "-i", ""]
        let pipe = Pipe()
        p.standardOutput = pipe
        p.standardError = pipe
        do { try p.run() } catch { return (1, 0) }
        p.waitUntilExit()
        let text = String(data: pipe.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
        var inAudio = false
        var screen = 1
        var mic = 0
        for line in text.components(separatedBy: .newlines) {
            if line.lowercased().contains("audio devices") { inAudio = true; continue }
            if line.lowercased().contains("video devices") { inAudio = false; continue }
            guard let idx = parseDeviceIndex(line) else { continue }
            let lower = line.lowercased()
            if !inAudio && lower.contains("capture screen") { screen = idx }
            if inAudio && (lower.contains("macbook") || lower.contains("microphone") || lower.contains("built-in")) {
                mic = idx
            }
        }
        return (screen, mic)
    }

    private static func parseDeviceIndex(_ line: String) -> Int? {
        guard let re = try? NSRegularExpression(pattern: "\\[(\\d+)\\]") else { return nil }
        let range = NSRange(line.startIndex..., in: line)
        let matches = re.matches(in: line, range: range)
        guard let last = matches.last, let r = Range(last.range(at: 1), in: line) else { return nil }
        return Int(line[r])
    }

    private static func ffmpegPath() -> String? {
        let candidates = [
            "/opt/homebrew/bin/ffmpeg",
            "/usr/local/bin/ffmpeg"
        ]
        for c in candidates where FileManager.default.isExecutableFile(atPath: c) {
            return c
        }
        return which("ffmpeg")
    }

    private static func ffmpegSibling(_ name: String) -> String? {
        if let ff = ffmpegPath() {
            let sib = (ff as NSString).deletingLastPathComponent + "/\(name)"
            if FileManager.default.isExecutableFile(atPath: sib) { return sib }
        }
        return which(name)
    }

    private static func which(_ name: String) -> String? {
        let p = Process()
        p.executableURL = URL(fileURLWithPath: "/usr/bin/which")
        p.arguments = [name]
        let out = Pipe()
        p.standardOutput = out
        p.standardError = FileHandle.nullDevice
        do { try p.run() } catch { return nil }
        p.waitUntilExit()
        let s = String(data: out.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8)?
            .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        return s.isEmpty ? nil : s
    }

    private static func timestamp() -> String {
        let f = DateFormatter()
        f.locale = Locale(identifier: "en_US_POSIX")
        f.dateFormat = "yyyy-MM-dd_HH-mm-ss"
        return f.string(from: Date())
    }
}
