import Foundation
import Testing

@testable import Trio

@Suite("Home Stats Panel Range") struct HomeStatsPanelRangeTests {
    /// 2026-09-18 15:30:00 UTC — deliberately mid-afternoon so `.today` and
    /// `.day` cannot coincide.
    private static let reference = Date(timeIntervalSince1970: 1_789_745_400)

    private static let day: TimeInterval = 24 * 3600

    // MARK: - startDate

    @Test("today starts at local midnight") func todayStartsAtMidnight() {
        let start = HomeStatsPanelRange.today.startDate(relativeTo: Self.reference)
        #expect(start == Calendar.current.startOfDay(for: Self.reference))
        #expect(start <= Self.reference)
    }

    @Test(
        "trailing ranges subtract their span",
        arguments: [
            (HomeStatsPanelRange.day, 1.0),
            (HomeStatsPanelRange.week, 7.0),
            (HomeStatsPanelRange.month, 30.0),
            (HomeStatsPanelRange.threeMonths, 90.0)
        ]
    )
    func trailingRangesSubtractSpan(range: HomeStatsPanelRange, days: Double) {
        let start = range.startDate(relativeTo: Self.reference)
        #expect(start == Self.reference.addingTimeInterval(-days * Self.day))
    }

    @Test("every range starts at or before the reference date") func rangesNeverStartInFuture() {
        for range in HomeStatsPanelRange.allCases {
            #expect(range.startDate(relativeTo: Self.reference) <= Self.reference)
        }
    }

    @Test("ranges are ordered from shortest to longest span") func rangesAreOrdered() {
        // .today is excluded: its span depends on the wall clock, and just after
        // midnight it is shorter than any trailing range.
        let trailing: [HomeStatsPanelRange] = [.day, .week, .month, .threeMonths]
        let starts = trailing.map { $0.startDate(relativeTo: Self.reference) }
        #expect(starts == starts.sorted(by: >))
    }

    @Test("today is never longer than the trailing day") func todayFitsInsideTrailingDay() {
        // Midnight is at most 24h back, so .today must start no earlier than .day.
        let today = HomeStatsPanelRange.today.startDate(relativeTo: Self.reference)
        let day = HomeStatsPanelRange.day.startDate(relativeTo: Self.reference)
        #expect(today >= day)
    }

    @Test("startDate defaults to now") func startDateDefaultsToNow() {
        let before = Date()
        let start = HomeStatsPanelRange.week.startDate()
        let after = Date()
        #expect(start >= before.addingTimeInterval(-7 * Self.day))
        #expect(start <= after.addingTimeInterval(-7 * Self.day))
    }

    // MARK: - Persistence

    @Test("raw values are stable") func rawValuesAreStable() {
        // These are persisted in TrioSettings; changing one silently resets the
        // stored preference on upgrade.
        #expect(HomeStatsPanelRange.today.rawValue == "today")
        #expect(HomeStatsPanelRange.day.rawValue == "day")
        #expect(HomeStatsPanelRange.week.rawValue == "week")
        #expect(HomeStatsPanelRange.month.rawValue == "month")
        #expect(HomeStatsPanelRange.threeMonths.rawValue == "threeMonths")
    }

    @Test("round-trips through Codable") func roundTripsThroughCodable() throws {
        for range in HomeStatsPanelRange.allCases {
            let data = try JSONEncoder().encode(range)
            let decoded = try JSONDecoder().decode(HomeStatsPanelRange.self, from: data)
            #expect(decoded == range)
        }
    }

    @Test("id matches rawValue") func idMatchesRawValue() {
        for range in HomeStatsPanelRange.allCases {
            #expect(range.id == range.rawValue)
        }
    }

    // MARK: - Wording

    @Test("all five ranges are offered") func allCasesPresent() {
        #expect(HomeStatsPanelRange.allCases.count == 5)
    }

    @Test("every range has non-empty, distinct wording") func wordingIsPopulated() {
        for range in HomeStatsPanelRange.allCases {
            #expect(!range.displayName.isEmpty)
            #expect(!range.possessiveName.isEmpty)
            #expect(!range.scopeName.isEmpty)
        }
        #expect(Set(HomeStatsPanelRange.allCases.map(\.displayName)).count == 5)
        #expect(Set(HomeStatsPanelRange.allCases.map(\.possessiveName)).count == 5)
        #expect(Set(HomeStatsPanelRange.allCases.map(\.scopeName)).count == 5)
    }
}
