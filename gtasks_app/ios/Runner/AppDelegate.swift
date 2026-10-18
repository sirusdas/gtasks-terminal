import Flutter
import UIKit
import WidgetKit

@main
@objc class AppDelegate: FlutterAppDelegate, FlutterImplicitEngineDelegate {
  private static let channelName = "com.gtasks.gtasks_app/widget"
  private static let appGroupId = "group.com.gtasks.gtasks_app"

  private var pendingAction: String?
  private var methodChannel: FlutterMethodChannel?

  override func application(
    _ application: UIApplication,
    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
  ) -> Bool {
    let result = super.application(application, didFinishLaunchingWithOptions: launchOptions)
    setupWidgetMethodChannel()
    return result
  }

  func didInitializeImplicitFlutterEngine(_ engineBridge: FlutterImplicitEngineBridge) {
    GeneratedPluginRegistrant.register(with: engineBridge.pluginRegistry)
    setupWidgetMethodChannel()
  }

  private func setupWidgetMethodChannel() {
    guard methodChannel == nil,
          let controller = window?.rootViewController as? FlutterViewController else {
      return
    }

    let channel = FlutterMethodChannel(name: AppDelegate.channelName, binaryMessenger: controller.binaryMessenger)
    self.methodChannel = channel

    channel.setMethodCallHandler { [weak self] (call, result) in
      guard let self = self else { return }
      switch call.method {
      case "updateWidget":
        if let args = call.arguments as? [String: Any],
           let tabsJson = args["tabsJson"] as? String {
          if let sharedDefaults = UserDefaults(suiteName: AppDelegate.appGroupId) {
            sharedDefaults.set(tabsJson, forKey: "tabs_json")
          }
        }
        if #available(iOS 14.0, *) {
          WidgetCenter.shared.reloadAllTimelines()
        }
        result(true)
      case "getInitialAction":
        let action = self.pendingAction
        self.pendingAction = nil
        result(action)
      default:
        result(FlutterMethodNotImplemented)
      }
    }

    if let pending = pendingAction {
      channel.invokeMethod("onActionReceived", arguments: pending)
      pendingAction = nil
    }
  }

  override func application(
    _ app: UIApplication,
    open url: URL,
    options: [UIApplication.OpenURLOptionsKey: Any] = [:]
  ) -> Bool {
    if url.scheme == "gtasks" {
      let host = url.host ?? ""
      let path = url.path.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
      let action: String
      if host == "open_task_editor" || path == "open_task_editor" {
        action = "open_task_editor"
      } else if host == "open_ai_chat" || path == "open_ai_chat" {
        action = "open_ai_chat"
      } else if host == "open_tab" || path.starts(with: "open_tab") {
        let tabId = URLComponents(url: url, resolvingAgainstBaseURL: false)?
          .queryItems?.first(where: { $0.name == "id" })?.value ?? ""
        action = "open_tab:\(tabId)"
      } else {
        action = host.isEmpty ? path : host
      }

      self.pendingAction = action
      self.methodChannel?.invokeMethod("onActionReceived", arguments: action)
      return true
    }
    return super.application(app, open: url, options: options)
  }
}
