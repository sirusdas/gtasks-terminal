import WidgetKit
import SwiftUI
import UIKit

// MARK: - Compatibility Modifier
extension View {
    func widgetBackground(_ backgroundView: some View) -> some View {
        if #available(iOSApplicationExtension 17.0, *) {
            return containerBackground(for: .widget) {
                backgroundView
            }
        } else {
            return background(backgroundView)
        }
    }
}

// MARK: - Models
struct WidgetTabInfo: Codable, Identifiable {
    var id: String
    var title: String
    var taskCount: Int
    var urgentCount: Int?
    var isUrgent: Bool?
    var tasks: [WidgetTaskItem]?
}

struct WidgetTaskItem: Codable, Identifiable {
    var id: String
    var title: String
    var isCompleted: Bool
    var priority: String?
    var due: String?
    var listTitle: String?
    var space: String?
}

// MARK: - Timeline Entry
struct GTasksWidgetEntry: TimelineEntry {
    let date: Date
    let tabs: [WidgetTabInfo]
    let activeTab: WidgetTabInfo?
}

// MARK: - Timeline Provider
struct GTasksTimelineProvider: TimelineProvider {
    private static let appGroupId = "group.com.gtasks.gtasks_app"

    func placeholder(in context: Context) -> GTasksWidgetEntry {
        let sample = WidgetTabInfo(
            id: "tab_all",
            title: "All Tasks",
            taskCount: 12,
            urgentCount: 3,
            isUrgent: true,
            tasks: [
                WidgetTaskItem(id: "1", title: "Complete code review", isCompleted: false, priority: "high", due: "Today", listTitle: "Work", space: "Backend"),
                WidgetTaskItem(id: "2", title: "Submit expenses", isCompleted: false, priority: "medium", due: "Tomorrow", listTitle: "Personal", space: nil)
            ]
        )
        return GTasksWidgetEntry(date: Date(), tabs: [sample], activeTab: sample)
    }

    func getSnapshot(in context: Context, completion: @escaping (GTasksWidgetEntry) -> Void) {
        completion(loadCurrentEntry())
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<GTasksWidgetEntry>) -> Void) {
        let entry = loadCurrentEntry()
        // Refresh every 30 minutes or when triggered by WidgetCenter
        let nextUpdate = Calendar.current.date(byAdding: .minute, value: 30, to: Date()) ?? Date()
        let timeline = Timeline(entries: [entry], policy: .after(nextUpdate))
        completion(timeline)
    }

    private func fallbackEntry() -> GTasksWidgetEntry {
        let sample = WidgetTabInfo(
            id: "tab_all",
            title: "All Tasks",
            taskCount: 0,
            urgentCount: 0,
            isUrgent: false,
            tasks: []
        )
        return GTasksWidgetEntry(date: Date(), tabs: [sample], activeTab: sample)
    }

    private func loadCurrentEntry() -> GTasksWidgetEntry {
        guard let sharedDefaults = UserDefaults(suiteName: GTasksTimelineProvider.appGroupId),
              let tabsJson = sharedDefaults.string(forKey: "tabs_json"),
              let data = tabsJson.data(using: .utf8) else {
            return fallbackEntry()
        }

        do {
            let tabs = try JSONDecoder().decode([WidgetTabInfo].self, from: data)
            let active = tabs.first
            return GTasksWidgetEntry(date: Date(), tabs: tabs, activeTab: active)
        } catch {
            return fallbackEntry()
        }
    }
}

// MARK: - SwiftUI Views
struct GTasksWidgetEntryView: View {
    var entry: GTasksTimelineProvider.Entry
    @Environment(\.widgetFamily) var family

    var body: some View {
        Group {
            switch family {
            case .systemSmall:
                SmallWidgetView(entry: entry)
            case .systemMedium:
                MediumWidgetView(entry: entry)
            case .systemLarge:
                LargeWidgetView(entry: entry)
            default:
                SmallWidgetView(entry: entry)
            }
        }
        .widgetBackground(Color(UIColor.systemBackground))
    }
}

// MARK: - Small Widget (Compact Card)
struct SmallWidgetView: View {
    let entry: GTasksWidgetEntry

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "checkmark.circle.fill")
                    .foregroundColor(.blue)
                    .font(.system(size: 16))
                Text("GTasks")
                    .font(.system(size: 12, weight: .bold))
                    .foregroundColor(.secondary)
                Spacer()
                if let urgent = entry.activeTab?.urgentCount, urgent > 0 {
                    Text("\(urgent)!")
                        .font(.system(size: 10, weight: .black))
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color.red.opacity(0.85))
                        .foregroundColor(.white)
                        .clipShape(Capsule())
                }
            }

            Spacer()

            Text("\(entry.activeTab?.taskCount ?? 0)")
                .font(.system(size: 38, weight: .heavy, design: .rounded))
                .foregroundColor(.primary)

            Text(entry.activeTab?.title ?? "All Tasks")
                .font(.system(size: 13, weight: .semibold))
                .lineLimit(1)
                .foregroundColor(.secondary)

            Link(destination: URL(string: "gtasks://open_task_editor")!) {
                HStack {
                    Image(systemName: "plus")
                        .font(.system(size: 11, weight: .bold))
                    Text("Add Task")
                        .font(.system(size: 11, weight: .bold))
                }
                .foregroundColor(.blue)
            }
        }
        .padding(12)
        .widgetURL(URL(string: "gtasks://open_tab?id=\(entry.activeTab?.id ?? "")"))
    }
}

// MARK: - Medium Widget (Header + Preview Tasks)
struct MediumWidgetView: View {
    let entry: GTasksWidgetEntry

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            // Header Row
            HStack {
                Image(systemName: "checkmark.circle.fill")
                    .foregroundColor(.blue)
                    .font(.system(size: 15))
                Text(entry.activeTab?.title ?? "GTasks")
                    .font(.system(size: 13, weight: .bold))
                    .lineLimit(1)

                Text("\(entry.activeTab?.taskCount ?? 0)")
                    .font(.system(size: 11, weight: .bold))
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Color.blue.opacity(0.15))
                    .foregroundColor(.blue)
                    .clipShape(Capsule())

                Spacer()

                Link(destination: URL(string: "gtasks://open_ai_chat")!) {
                    Image(systemName: "sparkles")
                        .font(.system(size: 13))
                        .foregroundColor(.orange)
                }

                Link(destination: URL(string: "gtasks://open_task_editor")!) {
                    Image(systemName: "plus.circle.fill")
                        .font(.system(size: 18))
                        .foregroundColor(.blue)
                }
            }

            Divider()

            // Tasks preview list
            let tasks = entry.activeTab?.tasks ?? []
            if tasks.isEmpty {
                Spacer()
                Text("No pending tasks in this view")
                    .font(.system(size: 12))
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity, alignment: .center)
                Spacer()
            } else {
                ForEach(tasks.prefix(3)) { task in
                    HStack(spacing: 6) {
                        Circle()
                            .strokeBorder(priorityColor(task.priority), lineWidth: 1.5)
                            .frame(width: 10, height: 10)

                        Text(task.title)
                            .font(.system(size: 12, weight: .medium))
                            .lineLimit(1)
                            .foregroundColor(.primary)

                        Spacer()

                        if let space = task.space {
                            Text(space)
                                .font(.system(size: 9, weight: .semibold))
                                .padding(.horizontal, 4)
                                .padding(.vertical, 1)
                                .background(Color.purple.opacity(0.12))
                                .foregroundColor(.purple)
                                .cornerRadius(3)
                        }

                        if let due = task.due {
                            Text(due)
                                .font(.system(size: 10))
                                .foregroundColor(.secondary)
                        }
                    }
                }
            }
        }
        .padding(12)
        .widgetURL(URL(string: "gtasks://open_tab?id=\(entry.activeTab?.id ?? "")"))
    }

    private func priorityColor(_ priority: String?) -> Color {
        switch priority?.lowercased() {
        case "critical": return .red
        case "high": return .orange
        case "low": return .gray
        default: return .blue
        }
    }
}

// MARK: - Large Widget (Full Dashboard View)
struct LargeWidgetView: View {
    let entry: GTasksWidgetEntry

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Header
            HStack {
                HStack(spacing: 6) {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(.blue)
                        .font(.system(size: 18))
                    Text("GTasks")
                        .font(.system(size: 15, weight: .bold))
                }

                Spacer()

                if let urgent = entry.activeTab?.urgentCount, urgent > 0 {
                    HStack(spacing: 3) {
                        Image(systemName: "flame.fill")
                            .font(.system(size: 10))
                        Text("\(urgent) Urgent")
                            .font(.system(size: 11, weight: .bold))
                    }
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(Color.red.opacity(0.15))
                    .foregroundColor(.red)
                    .cornerRadius(6)
                }

                Link(destination: URL(string: "gtasks://open_task_editor")!) {
                    Image(systemName: "plus.circle.fill")
                        .font(.system(size: 20))
                        .foregroundColor(.blue)
                }
            }

            // Tab bar chips preview
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 6) {
                    ForEach(entry.tabs) { tab in
                        HStack(spacing: 4) {
                            Text(tab.title)
                                .font(.system(size: 11, weight: .semibold))
                            Text("\(tab.taskCount)")
                                .font(.system(size: 9, weight: .bold))
                                .padding(.horizontal, 4)
                                .background(Color.secondary.opacity(0.2))
                                .clipShape(Capsule())
                        }
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(tab.id == entry.activeTab?.id ? Color.blue.opacity(0.15) : Color.secondary.opacity(0.08))
                        .foregroundColor(tab.id == entry.activeTab?.id ? .blue : .primary)
                        .cornerRadius(8)
                    }
                }
            }

            Divider()

            // Task list
            let tasks = entry.activeTab?.tasks ?? []
            if tasks.isEmpty {
                Spacer()
                Text("All tasks completed in this tab! 🎉")
                    .font(.system(size: 13))
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity, alignment: .center)
                Spacer()
            } else {
                VStack(spacing: 8) {
                    ForEach(tasks.prefix(6)) { task in
                        HStack(spacing: 8) {
                            Circle()
                                .strokeBorder(priorityColor(task.priority), lineWidth: 1.5)
                                .frame(width: 12, height: 12)

                            VStack(alignment: .leading, spacing: 2) {
                                Text(task.title)
                                    .font(.system(size: 12, weight: .medium))
                                    .lineLimit(1)
                                    .foregroundColor(.primary)

                                HStack(spacing: 4) {
                                    if let list = task.listTitle {
                                        Text(list)
                                            .font(.system(size: 9))
                                            .foregroundColor(.secondary)
                                    }
                                    if let space = task.space {
                                        Text("• \(space)")
                                            .font(.system(size: 9, weight: .semibold))
                                            .foregroundColor(.purple)
                                    }
                                }
                            }

                            Spacer()

                            if let due = task.due {
                                Text(due)
                                    .font(.system(size: 10, weight: .semibold))
                                    .foregroundColor(due.lowercased().contains("today") ? .orange : .secondary)
                            }
                        }
                        .padding(.vertical, 2)
                    }
                }
            }

            Spacer()

            // Footer Quick Action Bar
            HStack {
                Link(destination: URL(string: "gtasks://open_ai_chat")!) {
                    HStack(spacing: 4) {
                        Image(systemName: "sparkles")
                        Text("Ask AI")
                    }
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(.orange)
                }

                Spacer()

                Link(destination: URL(string: "gtasks://open_task_editor")!) {
                    HStack(spacing: 4) {
                        Image(systemName: "plus")
                        Text("New Task")
                    }
                    .font(.system(size: 11, weight: .bold))
                    .foregroundColor(.blue)
                }
            }
            .padding(.top, 4)
        }
        .padding(14)
        .widgetURL(URL(string: "gtasks://open_tab?id=\(entry.activeTab?.id ?? "")"))
    }

    private func priorityColor(_ priority: String?) -> Color {
        switch priority?.lowercased() {
        case "critical": return .red
        case "high": return .orange
        case "low": return .gray
        default: return .blue
        }
    }
}

// MARK: - Widget Definition
struct GTasksWidget: Widget {
    let kind: String = "GTasksWidget"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: GTasksTimelineProvider()) { entry in
            GTasksWidgetEntryView(entry: entry)
        }
        .configurationDisplayName("GTasks Dashboard")
        .description("View active tabs, task counts, and pending tasks at a glance.")
        .supportedFamilies([.systemSmall, .systemMedium, .systemLarge])
    }
}
