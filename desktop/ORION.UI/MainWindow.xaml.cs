using System;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;
using System.Windows;
using Microsoft.Web.WebView2.Core;

namespace ORION;

public partial class MainWindow : Window
{
    private static readonly Uri OrionUri = new("http://127.0.0.1:8890/v3/");
    private readonly HttpClient _http = new() { Timeout = TimeSpan.FromSeconds(2) };
    private bool _closing;

    public MainWindow()
    {
        InitializeComponent();
    }

    private async void Window_Loaded(object sender, RoutedEventArgs e)
    {
        try
        {
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

            OrionView.CoreWebView2.NavigationCompleted += (_, args) =>
            {
                Dispatcher.Invoke(() =>
                {
                    if (args.IsSuccess)
                    {
                        StartupOverlay.Visibility = Visibility.Collapsed;
                    }
                    else
                    {
                        StartupText.Text = "ORION UI failed to load · " + args.WebErrorStatus;
                        StartupOverlay.Visibility = Visibility.Visible;
                    }
                });
            };

            OrionView.Source = OrionUri;
        }
        catch (WebView2RuntimeNotFoundException)
        {
            StartupText.Text = "Microsoft WebView2 Runtime is required by the ORION desktop app.";
        }
        catch (Exception ex)
        {
            StartupText.Text = "ORION could not start · " + ex.Message;
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
