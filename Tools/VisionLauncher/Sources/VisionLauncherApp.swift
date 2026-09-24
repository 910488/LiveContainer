import SwiftUI
import UIKit

@main
struct VisionLauncherApp: App {
    var body: some Scene {
        WindowGroup {
            LauncherView()
        }
    }
}

private struct LauncherView: View {
    @State private var attempted = false
    @State private var status = "準備開啟 LiveContainer…"

    private var launchURL: URL? {
        guard let value = Bundle.main.object(forInfoDictionaryKey: "LCLaunchURL") as? String else { return nil }
        return URL(string: value)
    }

    private var guestDisplayName: String {
        Bundle.main.object(forInfoDictionaryKey: "CFBundleDisplayName") as? String ?? "Guest App"
    }

    var body: some View {
        VStack(spacing: 24) {
            Image(systemName: "play.rectangle.fill")
                .font(.system(size: 64))
                .foregroundStyle(.red)
            Text(guestDisplayName)
                .font(.largeTitle)
            Text(status)
            Button("再試一次", action: launch)
        }
        .padding(40)
        .onAppear {
            guard !attempted else { return }
            attempted = true
            launch()
        }
    }

    private func launch() {
        guard let url = launchURL else {
            status = "尚未設定目標 App"
            return
        }
        UIApplication.shared.open(url) { accepted in
            NSLog("VisionLauncher: openURL accepted=%@ url=%@", accepted.description, url.absoluteString)
            DispatchQueue.main.async {
                status = accepted ? "已交給 LiveContainer" : "無法開啟 LiveContainer"
            }
        }
    }
}
