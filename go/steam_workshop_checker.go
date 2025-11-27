package main

import (
	"bufio"
	"fmt"
	"io"
	"net/http"
	"os"
	"regexp"
	"strings"
	"time"
)

type WorkshopResult struct {
	ID    string
	Title string
	ModID string
}

var workshopResults = make(map[string]string)

func main() {
	fmt.Println("╔════════════════════════════════════════════════════════════════╗")
	fmt.Println("║        Steam Workshop Item Checker v1.0 (Go)                  ║")
	fmt.Println("║            (C) iamgue 2025                                    ║")
	fmt.Println("╚════════════════════════════════════════════════════════════════╝\n")

	scanner := bufio.NewScanner(os.Stdin)

	for {
		fmt.Println("\n📝 Steam Workshop IDs eingeben (getrennt mit ';'):")
		fmt.Println("💡 Beispiel: 2709866494;3445949422;3445362877")
		fmt.Println("💡 Tippe 'E' oder 'EXIT' zum Beenden")
		fmt.Print("➤ ")

		scanner.Scan()
		input := strings.TrimSpace(scanner.Text())

		if input == "" {
			fmt.Println("❌ Keine IDs eingegeben!")
			continue
		}

		if strings.ToUpper(input) == "E" || strings.ToUpper(input) == "EXIT" {
			fmt.Println("\n👋 Programm wird beendet...")
			break
		}

		ids := parseIDs(input)
		if len(ids) == 0 {
			fmt.Println("❌ Keine gültigen IDs gefunden!")
			continue
		}

		checkWorkshopIDs(ids)

		fmt.Println("\n🔍 Möchtest du deine Mod-IDs abgleichen? (j/n)")
		fmt.Print("➤ ")
		scanner.Scan()
		response := strings.ToLower(strings.TrimSpace(scanner.Text()))

		if response == "j" || response == "yes" || response == "y" {
			compareModIDs(scanner)
		}
	}
}

func parseIDs(input string) []string {
	var ids []string
	for _, id := range strings.Split(input, ";") {
		id = strings.TrimSpace(id)
		if id != "" && isNumeric(id) {
			ids = append(ids, id)
		}
	}
	return ids
}

func isNumeric(s string) bool {
	for _, c := range s {
		if c < '0' || c > '9' {
			return false
		}
	}
	return true
}

func checkWorkshopIDs(ids []string) {
	total := len(ids)
	var deleted, ok, errors, noTitle []string

	fmt.Printf("\n🔍 Überprüfe %d Workshop-Items...\n\n", total)
	fmt.Println(strings.Repeat("═", 100))

	workshopResults = make(map[string]string)

	for i, id := range ids {
		status, info, warning := checkWorkshopID(id)

		switch status {
		case "GELÖSCHT":
			deleted = append(deleted, id)
			fmt.Printf("\033[91m[%d/%d] ❌ GELÖSCHT: %s\033[0m\n", i+1, total, id)
		case "OK":
			ok = append(ok, id)
			if warning != "" {
				fmt.Printf("\033[92m[%d/%d] ✅ OK: %s - %s\033[0m\033[91m %s\033[0m\n", i+1, total, id, info, warning)
			} else {
				fmt.Printf("\033[92m[%d/%d] ✅ OK: %s - %s\033[0m\n", i+1, total, id, info)
			}
		case "NO_TITLE":
			noTitle = append(noTitle, id)
			fmt.Printf("\033[93m[%d/%d] ⚠️  WARNUNG: %s - Titel konnte nicht gelesen werden\033[0m\n", i+1, total, id)
		default:
			errors = append(errors, id)
			fmt.Printf("\033[91m[%d/%d] ⚠️  %s: %s - %s\033[0m\n", i+1, total, status, id, info)
		}

		time.Sleep(600 * time.Millisecond)
	}

	fmt.Println(strings.Repeat("═", 100))
	fmt.Println("\n📊 ZUSAMMENFASSUNG:\n")

	fmt.Printf("\033[92m✅ OK: %d\033[0m\n", len(ok))
	fmt.Printf("\033[93m⚠️  WARNUNG (kein Titel): %d\033[0m\n", len(noTitle))
	fmt.Printf("\033[91m❌ GELÖSCHT: %d\033[0m\n", len(deleted))
	fmt.Printf("\033[91m🚫 FEHLER: %d\033[0m\n\n", len(errors))

	if len(deleted) > 0 {
		fmt.Println("\033[91m🗑️  GELÖSCHTE MODs - Diese IDs entfernen:\033[0m")
		for _, id := range deleted {
			fmt.Printf("  %s\n", id)
		}
	}

	if len(noTitle) > 0 {
		fmt.Println("\033[93m\n⚠️  MODs OHNE TITEL (möglicherweise privat oder gelöscht):\033[0m")
		for _, id := range noTitle {
			fmt.Printf("  %s\n", id)
		}
	}

	if len(errors) > 0 {
		fmt.Println("\033[91m\n🚫 FEHLER bei diesen IDs (manuell überprüfen):\033[0m")
		for _, id := range errors {
			fmt.Printf("  %s\n", id)
		}
	}

	fmt.Println("\n" + strings.Repeat("═", 100))
}

func checkWorkshopID(id string) (string, string, string) {
	url := fmt.Sprintf("https://steamcommunity.com/sharedfiles/filedetails/?id=%s", id)

	resp, err := http.Get(url)
	if err != nil {
		return "FEHLER", err.Error(), ""
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return "GELÖSCHT", "", ""
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "FEHLER", err.Error(), ""
	}

	html := string(body)

	if strings.Contains(html, "This item has been deleted") || strings.Contains(html, "removed from the workshop") {
		return "GELÖSCHT", "", ""
	}

	title := extractTitle(html)
	if title == "" {
		return "NO_TITLE", "", ""
	}

	modID := extractModID(html)
	if modID != "" {
		workshopResults[id] = modID
		title = fmt.Sprintf("%s [ID: %s]", title, modID)
	}

	warning := ""
	if strings.Contains(strings.ToLower(title), "outdated") || strings.Contains(strings.ToLower(title), "working outdated") {
		warning = "[ACHTUNG OUTDATE]"
	}

	if strings.Contains(title, "B42") && !strings.Contains(title, "B41") {
		warning = "[ANDERE VERSION]"
	}

	return "OK", title, warning
}

func extractTitle(html string) string {
	re := regexp.MustCompile(`<div class="workshopItemTitle">(.*?)</div>`)
	matches := re.FindStringSubmatch(html)
	if len(matches) > 1 {
		title := strings.TrimSpace(matches[1])
		if title != "" {
			return title
		}
	}

	re = regexp.MustCompile(`<meta property="og:title" content="(.*?)"`)
	matches = re.FindStringSubmatch(html)
	if len(matches) > 1 {
		title := strings.TrimSpace(matches[1])
		if title != "" {
			return title
		}
	}

	return ""
}

func extractModID(html string) string {
	re := regexp.MustCompile(`Mod\s+ID:\s*([a-zA-Z0-9_\-\[\]]+)`)
	matches := re.FindStringSubmatch(html)
	if len(matches) > 1 {
		return strings.TrimSpace(matches[1])
	}

	re = regexp.MustCompile(`mod[""']?\s*:\s*[""']?([a-zA-Z0-9_\-]+)[""']?`)
	matches = re.FindStringSubmatch(html)
	if len(matches) > 1 {
		return strings.TrimSpace(matches[1])
	}

	return ""
}

func compareModIDs(scanner *bufio.Scanner) {
	fmt.Println("\n📋 Gib deine Mod-IDs ein (getrennt mit ';'):")
	fmt.Println("💡 Beispiel: iMeds;SCEEP_Hotwire;GreenHouse")
	fmt.Print("➤ ")

	scanner.Scan()
	input := strings.TrimSpace(scanner.Text())

	if input == "" {
		fmt.Println("❌ Keine Mod-IDs eingegeben!")
		return
	}

	var configModIDs []string
	for _, id := range strings.Split(input, ";") {
		id = strings.TrimSpace(id)
		if id != "" {
			configModIDs = append(configModIDs, id)
		}
	}

	fmt.Println("\n" + strings.Repeat("═", 100))
	fmt.Println("🔍 VERGLEICH DER MOD-IDs:\n")

	var workshopModIDs []string
	for _, modID := range workshopResults {
		workshopModIDs = append(workshopModIDs, modID)
	}

	found := 0
	missing := 0
	extra := 0

	for _, configModID := range configModIDs {
		if contains(workshopModIDs, configModID) {
			found++
			fmt.Printf("\033[92m✅ VORHANDEN: %s\033[0m\n", configModID)
		} else {
			missing++
			fmt.Printf("\033[91m❌ FEHLT: %s\033[0m\n", configModID)
		}
	}

	for workshopID, modID := range workshopResults {
		if !contains(configModIDs, modID) {
			extra++
			fmt.Printf("\033[93mℹ️  ZUSÄTZLICH: [%s] %s\033[0m\n", workshopID, modID)
		}
	}

	fmt.Println("\n" + strings.Repeat("═", 100))
	fmt.Println("\n📊 VERGLEICH-ZUSAMMENFASSUNG:\n")
	fmt.Printf("\033[92m✅ VORHANDEN: %d\033[0m\n", found)
	fmt.Printf("\033[91m❌ FEHLT: %d\033[0m\n", missing)
	fmt.Printf("\033[93mℹ️  ZUSÄTZLICH: %d\033[0m\n", extra)

	if missing > 0 {
		fmt.Println("\n\033[91m⚠️  FEHLENDE MODs (zu Config hinzufügen oder entfernen):\033[0m")
		for _, configModID := range configModIDs {
			if !contains(workshopModIDs, configModID) {
				fmt.Printf("  %s\n", configModID)
			}
		}
	}

	fmt.Println("\n" + strings.Repeat("═", 100))
}

func contains(slice []string, item string) bool {
	for _, v := range slice {
		if v == item {
			return true
		}
	}
	return false
}
