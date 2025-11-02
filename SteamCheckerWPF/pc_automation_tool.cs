using System;
using System.Windows.Forms;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;

namespace PCAutomationTool
{
    public partial class MainForm : Form
    {
        [DllImport("user32.dll")]
        private static extern void mouse_event(int dwFlags, int dx, int dy, int cButtons, int dwExtraInfo);
        private const int MOUSEEVENTF_MOVE = 0x0001;

        private Timer mainTimer;
        private bool isRunning = false;
        private int intervalMinutes = 10;
        private string textToType = "";

        public MainForm()
        {
            InitializeComponent();
            mainTimer = new Timer();
            mainTimer.Tick += MainTimer_Tick;
        }

        private void InitializeComponent()
        {
            this.Text = "PC Automation Tool";
            this.Width = 500;
            this.Height = 600;
            this.StartPosition = FormStartPosition.CenterScreen;
            this.BackColor = System.Drawing.Color.FromArgb(240, 240, 240);

            // Text Label
            Label lblText = new Label { Text = "Text eingeben:", Left = 20, Top = 20, Width = 100 };
            this.Controls.Add(lblText);

            // Text Input
            TextBox txtInput = new TextBox { Left = 20, Top = 45, Width = 440, Height = 60, Multiline = true, Name = "txtInput" };
            this.Controls.Add(txtInput);

            // Interval Label
            Label lblInterval = new Label { Text = "Intervall (Minuten):", Left = 20, Top = 120, Width = 150 };
            this.Controls.Add(lblInterval);

            // Interval Input
            NumericUpDown numInterval = new NumericUpDown { Left = 20, Top = 145, Width = 100, Value = 10, Minimum = 1, Maximum = 1440, Name = "numInterval" };
            this.Controls.Add(numInterval);

            // Start Button
            Button btnStart = new Button { Text = "START", Left = 20, Top = 190, Width = 200, Height = 50, BackColor = System.Drawing.Color.FromArgb(76, 175, 80), ForeColor = System.Drawing.Color.White, Font = new System.Drawing.Font("Arial", 12, System.Drawing.FontStyle.Bold), Name = "btnStart" };
            btnStart.Click += BtnStart_Click;
            this.Controls.Add(btnStart);

            // Stop Button
            Button btnStop = new Button { Text = "STOP", Left = 260, Top = 190, Width = 200, Height = 50, BackColor = System.Drawing.Color.FromArgb(244, 67, 54), ForeColor = System.Drawing.Color.White, Font = new System.Drawing.Font("Arial", 12, System.Drawing.FontStyle.Bold), Name = "btnStop", Enabled = false };
            btnStop.Click += BtnStop_Click;
            this.Controls.Add(btnStop);

            // Status Label
            Label lblStatus = new Label { Text = "Status: Gestoppt", Left = 20, Top = 260, Width = 440, Height = 30, BorderStyle = BorderStyle.Fixed3D, Name = "lblStatus" };
            this.Controls.Add(lblStatus);

            // Log Label
            Label lblLog = new Label { Text = "Log:", Left = 20, Top = 300, Width = 100 };
            this.Controls.Add(lblLog);

            // Log ListBox
            ListBox logBox = new ListBox { Left = 20, Top = 325, Width = 440, Height = 220, Name = "logBox" };
            this.Controls.Add(logBox);
        }

        private void BtnStart_Click(object sender, EventArgs e)
        {
            TextBox txtInput = (TextBox)this.Controls["txtInput"];
            NumericUpDown numInterval = (NumericUpDown)this.Controls["numInterval"];
            Button btnStart = (Button)sender;
            Button btnStop = this.Controls["btnStop"] as Button;
            Label lblStatus = this.Controls["lblStatus"] as Label;

            textToType = txtInput.Text;
            intervalMinutes = (int)numInterval.Value;

            if (string.IsNullOrWhiteSpace(textToType))
            {
                MessageBox.Show("Bitte geben Sie einen Text ein!");
                return;
            }

            isRunning = true;
            mainTimer.Interval = intervalMinutes * 60 * 1000;
            mainTimer.Start();

            btnStart.Enabled = false;
            btnStop.Enabled = true;
            lblStatus.Text = "Status: Läuft - nächste Eingabe in " + intervalMinutes + " Min.";
            AddLog("✓ Automation gestartet - Intervall: " + intervalMinutes + " Minuten");
            AddLog("✓ Text: '" + textToType + "'");
        }

        private void BtnStop_Click(object sender, EventArgs e)
        {
            isRunning = false;
            mainTimer.Stop();

            Button btnStart = this.Controls["btnStart"] as Button;
            Button btnStop = sender as Button;
            Label lblStatus = this.Controls["lblStatus"] as Label;

            btnStart.Enabled = true;
            btnStop.Enabled = false;
            lblStatus.Text = "Status: Gestoppt";
            AddLog("✗ Automation gestoppt");
        }

        // Make the timer tick handler async so the UI thread is not blocked during waits
        private async void MainTimer_Tick(object sender, EventArgs e)
        {
            if (!isRunning) return;

            try
            {
                // Text eingeben
                SendKeys.SendWait(textToType);
                SendKeys.SendWait("{ENTER}");

                AddLog("→ Text eingegeben: '" + textToType + "' + Enter");

                // Maus bewegen (kleine Bewegung) – non-blocking wait
                mouse_event(MOUSEEVENTF_MOVE, 5, 5, 0, 0);
                await Task.Delay(200).ConfigureAwait(true);
                mouse_event(MOUSEEVENTF_MOVE, -5, -5, 0, 0);

                // Taste drücken (Strg, wird meist ignoriert)
                SendKeys.SendWait("^");

                AddLog("→ PC aktiv gehalten (Maus + Taste)");

                Label lblStatus = this.Controls["lblStatus"] as Label;
                if (lblStatus != null)
                    lblStatus.Text = "Status: Läuft - letzte Aktion: " + DateTime.Now.ToString("HH:mm:ss");
            }
            catch (Exception ex)
            {
                AddLog("Fehler im Timer: " + ex.Message);
            }
        }

        private void AddLog(string message)
        {
            ListBox logBox = this.Controls["logBox"] as ListBox;
            if (logBox != null)
            {
                logBox.Items.Insert(0, "[" + DateTime.Now.ToString("HH:mm:ss") + "] " + message);
                if (logBox.Items.Count > 100)
                    logBox.Items.RemoveAt(logBox.Items.Count - 1);
            }
        }
    }

    static class Program
    {
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.Run(new MainForm());
        }
    }
}