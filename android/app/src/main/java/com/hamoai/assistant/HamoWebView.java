package com.hamoai.assistant;

import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import java.util.Objects;

/** Builds the WebView that shows the HAMO AI web UI (used by the app screen and the floating panel). */
final class HamoWebView {
    private HamoWebView() {}

    static WebView create(Context context, String serverUrl, Runnable onClose) {
        Context app = context.getApplicationContext();
        WebView webView = new WebView(context);
        webView.setBackgroundColor(0xFF0D1220);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setSupportZoom(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);

        webView.addJavascriptInterface(new HamoBridge(app, onClose), "HamoNative");
        webView.setWebViewClient(new Client(app, serverUrl));
        webView.loadUrl(serverUrl);
        return webView;
    }

    private static final class Client extends WebViewClient {
        private final Context app;
        private final String serverUrl;
        private final Uri base;

        Client(Context app, String serverUrl) {
            this.app = app;
            this.serverUrl = serverUrl;
            this.base = Uri.parse(serverUrl);
        }

        private boolean sameOrigin(Uri uri) {
            return Objects.equals(uri.getScheme(), base.getScheme())
                    && Objects.equals(uri.getHost(), base.getHost())
                    && uri.getPort() == base.getPort();
        }

        @Override
        public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
            Uri uri = request.getUrl();
            if (sameOrigin(uri)) {
                return false;
            }
            // Anything outside the HAMO AI server opens in the normal browser, never inside the panel.
            try {
                Intent intent = new Intent(Intent.ACTION_VIEW, uri);
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                app.startActivity(intent);
            } catch (Exception ignored) {
                // No browser available: do nothing.
            }
            return true;
        }

        @Override
        public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
            if (request.isForMainFrame()) {
                view.loadDataWithBaseURL(serverUrl, errorPage(), "text/html", "UTF-8", null);
            }
        }

        private String errorPage() {
            return "<html dir='rtl' lang='ar'><head>"
                    + "<meta name='viewport' content='width=device-width,initial-scale=1'></head>"
                    + "<body style='background:#0d1220;color:#eef1f8;font-family:sans-serif;"
                    + "padding:28px;text-align:center;line-height:1.9'>"
                    + "<h3>تعذر الاتصال بخادم HAMO AI</h3>"
                    + "<p style='color:#9aa5bd'>شغّل الخادم في Termux بالأمر:<br>"
                    + "<code style='direction:ltr;display:inline-block'>bash start.sh</code><br>"
                    + "ثم اضغط إعادة المحاولة.</p>"
                    + "<a href='" + serverUrl + "' style='display:inline-block;background:#536dfe;"
                    + "color:#fff;padding:12px 24px;border-radius:12px;text-decoration:none'>"
                    + "إعادة المحاولة</a></body></html>";
        }
    }
}
