using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using HtmlAgilityPack;

class SteamWorkshopChecker
{
    private static readonly HttpClient client = new HttpClient();
    private static int totalCount = 0;
    private static int currentCount = 0;
    private static Dictionary<string, string> workshopResults = new Dictionary<string, string>(); // ID → ModID

    static async Task Main(string[] args)
    {
        Console.OutputEncoding = System.Text.Encoding.UTF8;
        Console.WriteLine("╔════════════════════════════════════════════════════════════════╗");
        Console.WriteLine("║        Steam Workshop Item Checker v3.0     by iamgue          ║");
        Console.WriteLine("╚════════════════════════════════════════════════════════════════╝\n");

        client.DefaultRequestHeaders.Add("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36");

        while (true)
        {
            Console.WriteLine("\n📝 Steam Workshop IDs eingeben (getrennt mit ';'):");
            Console.WriteLine("💡 Beispiel: 2709866494;3445949422;3445362877");
            Console.WriteLine("💡 Tippe 'E' oder 'EXIT' zum Beenden");
            Console.Write("➤ ");
            
            string input = Console.ReadLine()?.Trim();
            
            if (string.IsNullOrEmpty(input))
            {
                Console.WriteLine("❌ Keine IDs eingegeben!");
                continue;
            }

            if (input.ToUpper() == "E")
            {
                Console.WriteLine("\n👋 Programm wird beendet...");
                break;
            }

            if (input.ToLower() == "exit" || input.ToLower() == "quit")
            {
                Console.WriteLine("\n👋 Auf Wiedersehen!");
                break;
            }

            var ids = input.Split(';')
                .Select(id => id.Trim())
                .Where(id => !string.IsNullOrEmpty(id) && id.All(char.IsDigit))
                .ToList();

            if (!ids.Any())
            {
                Console.WriteLine("❌ Keine gültigen IDs gefunden!");
                continue;
            }

            await CheckWorkshopIds(ids);

            // Nach dem ersten Check: Frage nach Mod-ID Vergleich
            Console.WriteLine("\n🔍 Möchtest du deine Mod-IDs abgleichen? (j/n)");
            Console.Write("➤ ");
            string compareInput = Console.ReadLine()?.Trim().ToLower();

            if (compareInput == "j" || compareInput == "yes" || compareInput == "y")
            {
                CompareModIds();
            }
        }
    }

    static async Task CheckWorkshopIds(List<string> ids)
    {
        totalCount = ids.Count;
        currentCount = 0;
        workshopResults.Clear();
        
        var deleted = new List<string>();
        var ok = new List<(string id, string title, string warning)>();
        var errors = new List<(string id, string error)>();
        var noTitle = new List<string>();

        Console.WriteLine($"\n🔍 Überprüfe {totalCount} Workshop-Items...\n");
        Console.WriteLine(new string('═', 120));

        foreach (var id in ids)
        {
            currentCount++;
            var (status, info, warning) = await CheckWorkshopId(id);

            if (status == "GELÖSCHT")
            {
                deleted.Add(id);
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine($"[{currentCount}/{totalCount}] ❌ GELÖSCHT: {id}");
                Console.ResetColor();
            }
            else if (status == "OK")
            {
                ok.Add((id, info, warning));
                
                if (!string.IsNullOrEmpty(warning))
                {
                    Console.ForegroundColor = ConsoleColor.Green;
                    Console.Write($"[{currentCount}/{totalCount}] ✅ OK: {id} - {info}");
                    Console.ForegroundColor = ConsoleColor.Red;
                    Console.WriteLine($" {warning}");
                    Console.ResetColor();
                }
                else
                {
                    Console.ForegroundColor = ConsoleColor.Green;
                    Console.WriteLine($"[{currentCount}/{totalCount}] ✅ OK: {id} - {info}");
                    Console.ResetColor();
                }
            }
            else if (status == "NO_TITLE")
            {
                noTitle.Add(id);
                Console.ForegroundColor = ConsoleColor.Yellow;
                Console.WriteLine($"[{currentCount}/{totalCount}] ⚠️  WARNUNG: {id} - Titel konnte nicht gelesen werden");
                Console.ResetColor();
            }
            else
            {
                errors.Add((id, info));
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine($"[{currentCount}/{totalCount}] ⚠️  {status}: {id} - {info}");
                Console.ResetColor();
            }

            await Task.Delay(600);
        }

        Console.WriteLine(new string('═', 120));
        Console.WriteLine("\n📊 ZUSAMMENFASSUNG:\n");
        
        Console.ForegroundColor = ConsoleColor.Green;
        Console.WriteLine($"✅ OK: {ok.Count}");
        Console.ResetColor();
        
        Console.ForegroundColor = ConsoleColor.Yellow;
        Console.WriteLine($"⚠️  WARNUNG (kein Titel): {noTitle.Count}");
        Console.ResetColor();
        
        Console.ForegroundColor = ConsoleColor.Red;
        Console.WriteLine($"❌ GELÖSCHT: {deleted.Count}");
        Console.ResetColor();
        
        Console.ForegroundColor = ConsoleColor.Red;
        Console.WriteLine($"🚫 FEHLER: {errors.Count}\n");
        Console.ResetColor();

        // Warnung-Summary
        var withWarnings = ok.Where(o => !string.IsNullOrEmpty(o.warning)).ToList();
        if (withWarnings.Any())
        {
            Console.ForegroundColor = ConsoleColor.Red;
            Console.WriteLine("⚠️  MODs MIT WARNUNGEN:");
            foreach (var (id, title, warning) in withWarnings)
            {
                Console.WriteLine($"  {id} - {title} {warning}");
            }
            Console.ResetColor();
            Console.WriteLine();
        }

        if (deleted.Any())
        {
            Console.ForegroundColor = ConsoleColor.Red;
            Console.WriteLine("🗑️  GELÖSCHTE MODs - Diese IDs entfernen:");
            foreach (var id in deleted)
            {
                Console.WriteLine($"  {id}");
            }
            Console.ResetColor();
        }

        if (noTitle.Any())
        {
            Console.ForegroundColor = ConsoleColor.Yellow;
            Console.WriteLine("\n⚠️  MODs OHNE TITEL (möglicherweise privat oder gelöscht):");
            foreach (var id in noTitle)
            {
                Console.WriteLine($"  {id}");
            }
            Console.ResetColor();
        }

        if (errors.Any())
        {
            Console.ForegroundColor = ConsoleColor.Red;
            Console.WriteLine("\n🚫 FEHLER bei diesen IDs (manuell überprüfen):");
            foreach (var (id, err) in errors)
            {
                Console.WriteLine($"  {id}: {err}");
            }
            Console.ResetColor();
        }

        Console.WriteLine("\n" + new string('═', 120));

        // ===== ABFRAGE: Mods mit Warnungen entfernen =====
        if (withWarnings.Any())
        {
            Console.WriteLine("\n❓ Möchtest du die Mods mit Warnungen aus deiner Liste entfernen?");
            Console.WriteLine("⚠️  Diese Mods werden gelöscht:");
            foreach (var (id, title, warning) in withWarnings)
            {
                Console.ForegroundColor = ConsoleColor.Yellow;
                Console.WriteLine($"  - {id}");
                Console.ResetColor();
            }
            Console.WriteLine("\n(j/n)");
            Console.Write("➤ ");
            
            string removeInput = Console.ReadLine()?.Trim().ToLower();

            if (removeInput == "j" || removeInput == "yes" || removeInput == "y")
            {
                var idsToRemove = withWarnings.Select(o => o.id).ToHashSet();
                var remainingIds = ok.Where(o => !idsToRemove.Contains(o.id)).Select(o => o.id).ToList();

                Console.WriteLine("\n" + new string('═', 120));
                Console.WriteLine("\n✅ AKTUALISIERTE LISTE (ohne Mods mit Warnungen):\n");
                
                if (remainingIds.Count > 0)
                {
                    Console.ForegroundColor = ConsoleColor.Green;
                    Console.WriteLine(string.Join(";", remainingIds));
                    Console.ResetColor();
                    Console.WriteLine($"\n📊 {remainingIds.Count} Mods in deiner Liste verbleibend");
                }
                else
                {
                    Console.ForegroundColor = ConsoleColor.Yellow;
                    Console.WriteLine("⚠️  Alle Mods werden entfernt!");
                    Console.ResetColor();
                }
                
                Console.WriteLine("\n" + new string('═', 120));
            }
        }
    }

    static void CompareModIds()
    {
        Console.WriteLine("\n📋 Gib deine Mod-IDs ein (getrennt mit ';'):");
        Console.WriteLine("💡 Beispiel: iMeds;SCEEP_Hotwire;GreenHouse");
        Console.Write("➤ ");

        string input = Console.ReadLine()?.Trim();

        if (string.IsNullOrEmpty(input))
        {
            Console.WriteLine("❌ Keine Mod-IDs eingegeben!");
            return;
        }

        var configModIds = input.Split(';')
            .Select(id => id.Trim())
            .Where(id => !string.IsNullOrEmpty(id))
            .ToList();

        Console.WriteLine("\n" + new string('═', 120));
        Console.WriteLine("🔍 VERGLEICH DER MOD-IDs:\n");

        var found = new List<string>();
        var missing = new List<string>();
        var extra = new List<(string workshopId, string modId)>();

        // Alle Workshop ModIds extrahieren
        var workshopModIds = workshopResults.Values.ToList();

        foreach (var configModId in configModIds)
        {
            if (workshopModIds.Contains(configModId))
            {
                found.Add(configModId);
                Console.ForegroundColor = ConsoleColor.Green;
                Console.WriteLine($"✅ VORHANDEN: {configModId}");
                Console.ResetColor();
            }
            else
            {
                missing.Add(configModId);
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine($"❌ FEHLT: {configModId}");
                Console.ResetColor();
            }
        }

        // Extra Workshop-Mods die nicht in der Config sind
        foreach (var kvp in workshopResults)
        {
            if (!configModIds.Contains(kvp.Value))
            {
                extra.Add((kvp.Key, kvp.Value));
            }
        }

        if (extra.Any())
        {
            Console.WriteLine();
            Console.ForegroundColor = ConsoleColor.Yellow;
            Console.WriteLine("ℹ️  ZUSÄTZLICHE Workshop-Mods (nicht in Config):");
            foreach (var (id, modId) in extra)
            {
                Console.WriteLine($"  [{id}] {modId}");
            }
            Console.ResetColor();
        }

        Console.WriteLine("\n" + new string('═', 120));
        Console.WriteLine("\n📊 VERGLEICH-ZUSAMMENFASSUNG:\n");

        Console.ForegroundColor = ConsoleColor.Green;
        Console.WriteLine($"✅ VORHANDEN: {found.Count}");
        Console.ResetColor();

        Console.ForegroundColor = ConsoleColor.Red;
        Console.WriteLine($"❌ FEHLT: {missing.Count}");
        Console.ResetColor();

        Console.ForegroundColor = ConsoleColor.Yellow;
        Console.WriteLine($"ℹ️  ZUSÄTZLICH: {extra.Count}");
        Console.ResetColor();

        if (missing.Any())
        {
            Console.ForegroundColor = ConsoleColor.Red;
            Console.WriteLine("\n⚠️  FEHLENDE MODs (zu Config hinzufügen oder entfernen):");
            foreach (var modId in missing)
            {
                Console.WriteLine($"  {modId}");
            }
            Console.ResetColor();
        }

        Console.WriteLine("\n" + new string('═', 120));
    }

    static async Task<(string status, string info, string warning)> CheckWorkshopId(string workshopId)
    {
        try
        {
            string url = $"https://steamcommunity.com/sharedfiles/filedetails/?id={workshopId}";
            
            var response = await client.GetAsync(url);

            if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
            {
                return ("GELÖSCHT", null, null);
            }

            string content = await response.Content.ReadAsStringAsync();

            if (content.Contains("This item has been deleted") || content.Contains("removed from the workshop"))
            {
                return ("GELÖSCHT", null, null);
            }

            // HTML Parser
            var doc = new HtmlDocument();
            doc.LoadHtml(content);

            // Versuche den Titel zu finden
            var titleNode = doc.DocumentNode.SelectSingleNode("//div[@class='workshopItemTitle']");
            
            string title = null;
            if (titleNode != null)
            {
                title = titleNode.InnerText?.Trim() ?? "Unbekannt";
                if (string.IsNullOrEmpty(title) || title.Length == 0)
                    title = null;
            }

            // Alternative: Meta-Tags
            if (title == null)
            {
                var ogTitle = doc.DocumentNode.SelectSingleNode("//meta[@property='og:title']");
                if (ogTitle != null)
                {
                    title = ogTitle.GetAttributeValue("content", "");
                    if (string.IsNullOrEmpty(title))
                        title = null;
                }
            }

            if (title == null)
            {
                return ("NO_TITLE", null, null);
            }

            // Suche nach Mod ID
            string modId = ExtractModId(content);
            if (!string.IsNullOrEmpty(modId))
            {
                workshopResults[workshopId] = modId;
                title = $"{title} [ID: {modId}]";
            }

            // Überprüfe auf Warnungen
            string warning = null;

            // Warnung 1: "Working Outdated" → ROT + [ACHTUNG OUTDATE]
            if (title.Contains("Outdated", StringComparison.OrdinalIgnoreCase) || 
                title.Contains("Working Outdated", StringComparison.OrdinalIgnoreCase))
            {
                warning = "[ACHTUNG OUTDATE]";
            }

            // Warnung 2: Nur "B42" im Titel → MAGENTA/VIOLETT + [ANDERE VERSION]
            if (title.Contains("B42") && !title.Contains("B41"))
            {
                warning = "[ANDERE VERSION]";
            }

            return ("OK", title, warning);
        }
        catch (HttpRequestException ex)
        {
            return ("FEHLER", ex.Message, null);
        }
        catch (TaskCanceledException)
        {
            return ("TIMEOUT", "Anfrage hat zu lange gedauert", null);
        }
        catch (Exception ex)
        {
            return ("FEHLER", ex.Message, null);
        }
    }

    static string ExtractModId(string htmlContent)
    {
        // Suche GENAU nach: Mod ID: " iMeds" (mit Anführungszeichen und Zeilenumbruch möglich)
        var match = Regex.Match(htmlContent, @"<b>Mod\s+ID:</b>\s*=\s*[""']([a-zA-Z0-9_\-\[\]]+)[""']", RegexOptions.IgnoreCase | RegexOptions.Singleline);
        if (match.Success)
        {
            return match.Groups[1].Value.Trim();
        }

        // Fallback: Mod ID: direkt gefolgt von Text in Anführungszeichen
        match = Regex.Match(htmlContent, @"Mod\s+ID[:\s]*[""']([a-zA-Z0-9_\-\[\]]+)[""']", RegexOptions.IgnoreCase);
        if (match.Success)
        {
            return match.Groups[1].Value.Trim();
        }

        // Fallback: Mod ID: gefolgt von Text (ohne Anführungszeichen)
        match = Regex.Match(htmlContent, @"Mod\s+ID:\s*([a-zA-Z0-9_\-\[\]]+)", RegexOptions.IgnoreCase);
        if (match.Success)
        {
            string result = match.Groups[1].Value.Trim();
            if (result != "=" && result != "$0")
                return result;
        }

        return null;
    }
}