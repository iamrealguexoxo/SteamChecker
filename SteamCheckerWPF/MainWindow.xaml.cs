using System;
using System.Collections.ObjectModel;
using System.Linq;
using System.Net.Http;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using System.Windows;
using HtmlAgilityPack;

namespace SteamCheckerWPF
{
    public partial class MainWindow : Window
    {
        private static readonly HttpClient client = new HttpClient();
        private ObservableCollection<WorkshopResult> results = new ObservableCollection<WorkshopResult>();

        public MainWindow()
        {
            InitializeComponent();
            ResultsGrid.ItemsSource = results;
            client.DefaultRequestHeaders.Add("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36");
        }

        private async void CheckButton_Click(object sender, RoutedEventArgs e)
        {
            string input = InputTextBox.Text.Trim();
            if (string.IsNullOrEmpty(input))
            {
                MessageBox.Show("Bitte gib mindestens eine ID ein!", "Warnung", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            var ids = input.Split(';')
                .Select(id => id.Trim())
                .Where(id => !string.IsNullOrEmpty(id) && id.All(char.IsDigit))
                .ToList();

            if (!ids.Any())
            {
                MessageBox.Show("Keine gültigen IDs gefunden!", "Fehler", MessageBoxButton.OK, MessageBoxImage.Error);
                return;
            }

            results.Clear();
            CheckButton.IsEnabled = false;
            StatusText.Text = "Überprüfe...";

            await CheckWorkshopIds(ids);

            CheckButton.IsEnabled = true;
            StatusText.Text = "✅ Überprüfung abgeschlossen!";
        }

        private async Task CheckWorkshopIds(System.Collections.Generic.List<string> ids)
        {
            int ok = 0, deleted = 0, errors = 0, warning = 0;

            foreach (var id in ids)
            {
                var (status, info, warn) = await CheckWorkshopId(id);

                var result = new WorkshopResult
                {
                    Id = id,
                    Status = status,
                    Title = info.Item1,
                    ModId = info.Item2,
                    Warning = warn
                };

                results.Add(result);

                if (status == "✅ OK") ok++;
                else if (status == "❌ GELÖSCHT") deleted++;
                else if (status == "🚫 FEHLER") errors++;
                else if (status == "⚠️ WARNUNG") warning++;

                await Task.Delay(300);
            }

            OkCount.Text = ok.ToString();
            DeletedCount.Text = deleted.ToString();
            ErrorCount.Text = errors.ToString();
            WarningCount.Text = warning.ToString();
        }

        private async Task<(string status, (string title, string modId) info, string warning)> CheckWorkshopId(string workshopId)
        {
            try
            {
                string url = $"https://steamcommunity.com/sharedfiles/filedetails/?id={workshopId}";
                var response = await client.GetAsync(url);

                if (!response.IsSuccessStatusCode)
                    return ("❌ GELÖSCHT", ("", ""), "");

                string html = await response.Content.ReadAsStringAsync();

                if (html.Contains("This item has been deleted") || html.Contains("removed from the workshop"))
                    return ("❌ GELÖSCHT", ("", ""), "");

                var doc = new HtmlDocument();
                doc.LoadHtml(html);

                var titleNode = doc.DocumentNode.SelectSingleNode("//div[@class='workshopItemTitle']");
                string title = titleNode?.InnerText?.Trim() ?? "";

                if (string.IsNullOrEmpty(title))
                {
                    var ogTitle = doc.DocumentNode.SelectSingleNode("//meta[@property='og:title']");
                    title = ogTitle?.GetAttributeValue("content", "") ?? "";
                }

                if (string.IsNullOrEmpty(title))
                    return ("⚠️ WARNUNG", ("Kein Titel", ""), "");

                string modId = ExtractModId(html);
                string warning = "";

                if (title.ToLower().Contains("outdated") || title.ToLower().Contains("working outdated"))
                    warning = "[ACHTUNG OUTDATE]";

                if (title.Contains("B42") && !title.Contains("B41"))
                    warning = "[ANDERE VERSION]";

                return ("✅ OK", (title, modId), warning);
            }
            catch
            {
                return ("🚫 FEHLER", ("", ""), "");
            }
        }

        private string ExtractModId(string htmlContent)
        {
            var match = Regex.Match(htmlContent, @"<b>Mod\s+ID:</b>\s*=\s*[""']([a-zA-Z0-9_\-\[\]]+)[""']", RegexOptions.IgnoreCase | RegexOptions.Singleline);
            if (match.Success)
                return match.Groups[1].Value.Trim();

            match = Regex.Match(htmlContent, @"Mod\s+ID[:\s]*[""']([a-zA-Z0-9_\-\[\]]+)[""']", RegexOptions.IgnoreCase);
            if (match.Success)
                return match.Groups[1].Value.Trim();

            match = Regex.Match(htmlContent, @"Mod\s+ID:\s*([a-zA-Z0-9_\-\[\]]+)", RegexOptions.IgnoreCase);
            if (match.Success)
            {
                string result = match.Groups[1].Value.Trim();
                if (result != "=" && result != "$0")
                    return result;
            }

            return "";
        }

        private void CompareButton_Click(object sender, RoutedEventArgs e)
        {
            string configModIds = ConfigModsTextBox.Text.Trim();
            if (string.IsNullOrEmpty(configModIds))
            {
                MessageBox.Show("Bitte gib Mod-IDs ein!", "Warnung", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            var configIds = configModIds.Split(';').Select(id => id.Trim()).Where(id => !string.IsNullOrEmpty(id)).ToList();
            var workshopModIds = results.Where(r => !string.IsNullOrEmpty(r.ModId)).Select(r => r.ModId).ToList();

            string compareText = "";
            int found = 0, missing = 0, extra = 0;

            foreach (var configId in configIds)
            {
                if (workshopModIds.Contains(configId))
                {
                    compareText += $"✅ VORHANDEN: {configId}\n";
                    found++;
                }
                else
                {
                    compareText += $"❌ FEHLT: {configId}\n";
                    missing++;
                }
            }

            foreach (var result in results)
            {
                if (!string.IsNullOrEmpty(result.ModId) && !configIds.Contains(result.ModId))
                {
                    compareText += $"ℹ️ ZUSÄTZLICH: [{result.Id}] {result.ModId}\n";
                    extra++;
                }
            }

            compareText += $"\n📊 ZUSAMMENFASSUNG:\n";
            compareText += $"✅ Vorhanden: {found}\n";
            compareText += $"❌ Fehlt: {missing}\n";
            compareText += $"ℹ️ Zusätzlich: {extra}";

            CompareResultsBox.Text = compareText;
            CompareResultsHeader.Visibility = Visibility.Visible;
            CompareResultsBox.Visibility = Visibility.Visible;
        }

        private void ExportButton_Click(object sender, RoutedEventArgs e)
        {
            string data = "Workshop ID\tMod ID\tStatus\tTitel\n";
            foreach (var result in results)
            {
                data += $"{result.Id}\t{result.ModId}\t{result.Status}\t{result.Title}\n";
            }

            string path = System.IO.Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.Desktop),
                $"steam_check_{DateTime.Now:yyyy-MM-dd_HH-mm-ss}.txt"
            );

            System.IO.File.WriteAllText(path, data);
            MessageBox.Show($"✅ Datei gespeichert!\n\n{path}", "Erfolg", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void CopyButton_Click(object sender, RoutedEventArgs e)
        {
            var ids = string.Join(";", results.Select(r => r.Id));
            Clipboard.SetText(ids);
            MessageBox.Show("✅ Workshop-IDs kopiert!", "Erfolg", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void ClearButton_Click(object sender, RoutedEventArgs e)
        {
            InputTextBox.Clear();
            results.Clear();
            OkCount.Text = "0";
            DeletedCount.Text = "0";
            ErrorCount.Text = "0";
            WarningCount.Text = "0";
            StatusText.Text = "";
        }
    }

    public class WorkshopResult
    {
        public string Id { get; set; }
        public string Status { get; set; }
        public string Title { get; set; }
        public string ModId { get; set; }
        public string Warning { get; set; }
    }
}
