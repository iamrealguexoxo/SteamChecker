import requests
import re
from time import sleep

class SteamWorkshopChecker:
    def __init__(self):
        self.workshop_results = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def main(self):
        print("╔════════════════════════════════════════════════════════════════╗")
        print("║        Steam Workshop Item Checker v1.0 (Python)              ║")
        print("╚════════════════════════════════════════════════════════════════╝\n")

        while True:
            print("\n📝 Steam Workshop IDs eingeben (getrennt mit ';'):")
            print("💡 Beispiel: 2709866494;3445949422;3445362877")
            
            user_input = input("➤ ").strip()

            if not user_input:
                print("❌ Keine IDs eingegeben!")
                continue

            if user_input.lower() in ["exit", "quit"]:
                print("\n👋 Auf Wiedersehen!")
                break

            ids = [
                id.strip() for id in user_input.split(';')
                if id.strip() and id.strip().isdigit()
            ]

            if not ids:
                print("❌ Keine gültigen IDs gefunden!")
                continue

            self.check_workshop_ids(ids)

            print("\n🔍 Möchtest du deine Mod-IDs abgleichen? (j/n)")
            compare_input = input("➤ ").strip().lower()

            if compare_input in ["j", "yes", "y"]:
                self.compare_mod_ids()

    def check_workshop_ids(self, ids):
        total = len(ids)
        deleted = []
        ok = []
        errors = []
        no_title = []

        print(f"\n🔍 Überprüfe {total} Workshop-Items...\n")
        print("═" * 100)

        self.workshop_results.clear()

        for current, workshop_id in enumerate(ids, 1):
            status, info, warning = self.check_workshop_id(workshop_id)

            if status == "GELÖSCHT":
                deleted.append(workshop_id)
                print(f"\033[91m[{current}/{total}] ❌ GELÖSCHT: {workshop_id}\033[0m")
            
            elif status == "OK":
                ok.append((workshop_id, info, warning))
                if warning:
                    print(f"\033[92m[{current}/{total}] ✅ OK: {workshop_id} - {info}\033[0m\033[91m {warning}\033[0m")
                else:
                    print(f"\033[92m[{current}/{total}] ✅ OK: {workshop_id} - {info}\033[0m")
            
            elif status == "NO_TITLE":
                no_title.append(workshop_id)
                print(f"\033[93m[{current}/{total}] ⚠️  WARNUNG: {workshop_id} - Titel konnte nicht gelesen werden\033[0m")
            
            else:
                errors.append((workshop_id, info))
                print(f"\033[91m[{current}/{total}] ⚠️  {status}: {workshop_id} - {info}\033[0m")

            sleep(0.6)

        print("═" * 100)
        print("\n📊 ZUSAMMENFASSUNG:\n")

        print(f"\033[92m✅ OK: {len(ok)}\033[0m")
        print(f"\033[93m⚠️  WARNUNG (kein Titel): {len(no_title)}\033[0m")
        print(f"\033[91m❌ GELÖSCHT: {len(deleted)}\033[0m")
        print(f"\033[91m🚫 FEHLER: {len(errors)}\033[0m\n")

        with_warnings = [(id, title, warn) for id, title, warn in ok if warn]
        if with_warnings:
            print("\033[91m⚠️  MODs MIT WARNUNGEN:\033[0m")
            for workshop_id, title, warning in with_warnings:
                print(f"  {workshop_id} - {title} {warning}")
            print()

        if deleted:
            print("\033[91m🗑️  GELÖSCHTE MODs - Diese IDs entfernen:\033[0m")
            for workshop_id in deleted:
                print(f"  {workshop_id}")

        if no_title:
            print("\033[93m\n⚠️  MODs OHNE TITEL (möglicherweise privat oder gelöscht):\033[0m")
            for workshop_id in no_title:
                print(f"  {workshop_id}")

        if errors:
            print("\033[91m\n🚫 FEHLER bei diesen IDs (manuell überprüfen):\033[0m")
            for workshop_id, err in errors:
                print(f"  {workshop_id}: {err}")

        print("\n" + "═" * 100)

    def check_workshop_id(self, workshop_id):
        url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={workshop_id}"

        try:
            response = self.session.get(url, timeout=10)

            if response.status_code != 200:
                return ("GELÖSCHT", None, None)

            html = response.text

            if "This item has been deleted" in html or "removed from the workshop" in html:
                return ("GELÖSCHT", None, None)

            # Extract Titel
            title = self.extract_title(html)
            if not title:
                return ("NO_TITLE", None, None)

            # Extract Mod ID
            mod_id = self.extract_mod_id(html)

            final_title = title
            if mod_id:
                final_title = f"{title} [ID: {mod_id}]"
                self.workshop_results[workshop_id] = mod_id

            warning = None

            if "outdated" in title.lower() or "working outdated" in title.lower():
                warning = "[ACHTUNG OUTDATE]"

            if "B42" in title and "B41" not in title:
                warning = "[ANDERE VERSION]"

            return ("OK", final_title, warning)

        except requests.exceptions.Timeout:
            return ("FEHLER", "Anfrage hat zu lange gedauert", None)
        except requests.exceptions.RequestException as e:
            return ("FEHLER", str(e), None)
        except Exception as e:
            return ("FEHLER", str(e), None)

    def extract_title(self, html):
        # Versuche den Titel aus workshopItemTitle zu extrahieren
        match = re.search(r'<div class="workshopItemTitle">(.*?)</div>', html)
        if match:
            title = match.group(1).strip()
            if title:
                return title

        # Fallback: OG-Tags
        match = re.search(r'<meta property="og:title" content="(.*?)"', html)
        if match:
            title = match.group(1).strip()
            if title:
                return title

        return None

    def extract_mod_id(self, html):
        # Suche nach: Mod ID: [beliebiger text]
        match = re.search(r'Mod\s+ID:\s*([a-zA-Z0-9_\-\[\]]+)', html)
        if match:
            return match.group(1).strip()

        # Fallback: Suche nach mod.info oder ähnliches
        match = re.search(r'mod[""\'\']\s*:\s*[""\'\'](.*?)[""\'\']+', html, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        return None

    def compare_mod_ids(self):
        print("\n📋 Gib deine Mod-IDs ein (getrennt mit ';'):")
        print("💡 Beispiel: iMeds;SCEEP_Hotwire;GreenHouse")
        
        user_input = input("➤ ").strip()

        if not user_input:
            print("❌ Keine Mod-IDs eingegeben!")
            return

        config_mod_ids = [
            id.strip() for id in user_input.split(';')
            if id.strip()
        ]

        print("\n" + "═" * 100)
        print("🔍 VERGLEICH DER MOD-IDs:\n")

        workshop_mod_ids = list(self.workshop_results.values())

        found = 0
        missing = 0
        extra = 0

        for config_mod_id in config_mod_ids:
            if config_mod_id in workshop_mod_ids:
                found += 1
                print(f"\033[92m✅ VORHANDEN: {config_mod_id}\033[0m")
            else:
                missing += 1
                print(f"\033[91m❌ FEHLT: {config_mod_id}\033[0m")

        for workshop_id, mod_id in self.workshop_results.items():
            if mod_id not in config_mod_ids:
                extra += 1
                print(f"\033[93mℹ️  ZUSÄTZLICH: [{workshop_id}] {mod_id}\033[0m")

        print("\n" + "═" * 100)
        print("\n📊 VERGLEICH-ZUSAMMENFASSUNG:\n")
        print(f"\033[92m✅ VORHANDEN: {found}\033[0m")
        print(f"\033[91m❌ FEHLT: {missing}\033[0m")
        print(f"\033[93mℹ️  ZUSÄTZLICH: {extra}\033[0m")

        if missing > 0:
            print("\n\033[91m⚠️  FEHLENDE MODs (zu Config hinzufügen oder entfernen):\033[0m")
            for config_mod_id in config_mod_ids:
                if config_mod_id not in workshop_mod_ids:
                    print(f"  {config_mod_id}")

        print("\n" + "═" * 100)


if __name__ == "__main__":
    checker = SteamWorkshopChecker()
    checker.main()
