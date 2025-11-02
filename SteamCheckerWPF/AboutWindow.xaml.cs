using System.Diagnostics;
using System.Reflection;
using System.Windows;
using System.Windows.Navigation;

namespace SteamCheckerWPF
{
    public partial class AboutWindow : Window
    {
        public AboutWindow()
        {
            InitializeComponent();
            VersionText.Text = $"v{GetVersionString()}";
        }

        private void Close_Click(object sender, RoutedEventArgs e)
        {
            this.Close();
        }

        private void Hyperlink_RequestNavigate(object sender, RequestNavigateEventArgs e)
        {
            try
            {
                Process.Start(new ProcessStartInfo(e.Uri.AbsoluteUri) { UseShellExecute = true });
            }
            catch
            {
                MessageBox.Show("Konnte den Browser nicht öffnen.", "Fehler", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

    internal static string GetVersionString()
    {
        try
        {
            var asm = Assembly.GetExecutingAssembly();
            // Prefer InformationalVersion (supports semver + pre-release)
            var info = asm.GetCustomAttribute<AssemblyInformationalVersionAttribute>()?.InformationalVersion;
            if (!string.IsNullOrWhiteSpace(info)) return info;

            var file = asm.GetCustomAttribute<AssemblyFileVersionAttribute>()?.Version;
            if (!string.IsNullOrWhiteSpace(file)) return file;

            var ver = asm.GetName().Version?.ToString(3);
            return string.IsNullOrWhiteSpace(ver) ? "1.0.0" : ver!;
        }
        catch
        {
            return "1.0.0";
        }
    }
}
}
