using System;
using System.IO;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows;
using Microsoft.Web.WebView2.Core;

namespace ORION;

public partial class MainWindow : Window
{
    private static readonly Uri OrionUri = new("http://127.0.0.1:8890/v3/");
    private readonly HttpClient _http = new() { Timeout = TimeSpan.FromSeconds(2) };
    private readonly string _stateRoot = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "ORION-V3"
    );
    private string ReadyFile => Path.Combine(_stateRoot, "desktop-ready.json");
    private string ErrorFile => Path.Combine(_stateRoot, "desktop-error.log");
    private bool _closing;

    public MainWindow()
    {
        InitializeComponent();
        OrionView.DefaultBackgroundColor = System.Drawing.Color.FromArgb(5, 7, 11);
    }

    private async void Window_Loaded(object sender, RoutedEventArgs e)
    {
        try
        {
            Directory.CreateDirectory(_stateRoot);
            TryDelete(ReadyFile);
            TryDelete(ErrorFile);

            StartupText.Text = "Connecting to ORION runtime…";
            await WaitForRuntimeAsync();

            StartupText.Text = "Loading STRATA…";
            var userData = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "ORION-V3",
                "WebView2"
            );
            Directory.CreateDirectory(userData);

            var environment = await CoreWebView2Environment.CreateAsync(
                browserExecutableFolder: null,
                userDataFolder: userData
            );

            await OrionView.EnsureCoreWebView2Async(environment);

            OrionView.CoreWebView2.Settings.AreDevToolsEnabled = false;
            OrionView.CoreWebView2.Settings.AreDefaultContextMenusEnabled = false;
            OrionView.CoreWebView2.Settings.IsStatusBarEnabled = false;
            OrionView.CoreWebView2.Settings.IsZoomControlEnabled = false;
            OrionView.CoreWebView2.Settings.AreBrowserAcceleratorKeysEnabled = false;

            OrionView.CoreWebView2.WebMessageReceived += (_, args) =>
            {
                if (string.Equals(args.TryGetWebMessageAsString(), "orion-close", StringComparison.Ordinal))
                {
                    Dispatcher.Invoke(Close);
                }
            };

            OrionView.CoreWebView2.NavigationCompleted += (_, args) =>
            {
                Dispatcher.Invoke(() =>
                {
                    if (args.IsSuccess)
                    {
                        OrionView.Visibility = Visibility.Visible;
                        StartupOverlay.Visibility = Visibility.Collapsed;
                        WriteReadyEvidence();
                    }
                    else
                    {
                        var detail = "ORION UI failed to load · " + args.WebErrorStatus;
                        StartupText.Text = detail;
                        StartupOverlay.Visibility = Visibility.Visible;
                        File.WriteAllText(ErrorFile, detail);
                    }
                });
            };

            OrionView.Source = OrionUri;
        }
        catch (WebView2RuntimeNotFoundException)
        {
            const string detail = "Microsoft WebView2 Runtime is required by the ORION desktop app.";
            StartupText.Text = detail;
            File.WriteAllText(ErrorFile, detail);
        }
        catch (Exception ex)
        {
            var detail = "ORION could not start · " + ex.Message;
            StartupText.Text = detail;
            File.WriteAllText(ErrorFile, detail);
        }
    }

    private void WriteReadyEvidence()
    {
        var evidence = new
        {
            schema = "orion-v3.desktop-ready/1",
            pid = Environment.ProcessId,
            url = OrionUri.ToString(),
            ready_at = DateTimeOffset.Now.ToString("O")
        };

        File.WriteAllText(
            ReadyFile,
            JsonSerializer.Serialize(evidence, new JsonSerializerOptions { WriteIndented = true })
        );
    }

    private static void TryDelete(string path)
    {
        try
        {
            if (File.Exists(path))
            {
                File.Delete(path);
            }
        }
        catch
        {
        }
    }

    private async Task WaitForRuntimeAsync()
    {
        Exception? last = null;

        for (var i = 0; i < 40; i++)
        {
            try
            {
                using var response = await _http.GetAsync("http://127.0.0.1:8890/api/health");
                if (response.IsSuccessStatusCode)
                {
                    return;
                }
            }
            catch (Exception ex)
            {
                last = ex;
            }

            await Task.Delay(250);
        }

        throw new InvalidOperationException(
            "ORION runtime did not become healthy on port 8890.",
            last
        );
    }

    private void Window_Closing(object? sender, System.ComponentModel.CancelEventArgs e)
    {
        if (_closing)
        {
            return;
        }

        _closing = true;
        TryDelete(ReadyFile);

        try
        {
            OrionView.CoreWebView2?.Stop();
            OrionView.Dispose();
        }
        catch
        {
            // Closing must remain best-effort; lifecycle cleanup is owned by START ORION.
        }
    }
}
