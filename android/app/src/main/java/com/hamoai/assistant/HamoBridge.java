package com.hamoai.assistant;

import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.webkit.JavascriptInterface;

/**
 * Methods the web UI can call as window.HamoNative.*
 * Exposed only to pages loaded from the configured HAMO AI server (see HamoWebView).
 */
final class HamoBridge {
    private final Context context;
    private final Runnable onClose;
    private final Handler main = new Handler(Looper.getMainLooper());

    HamoBridge(Context context, Runnable onClose) {
        this.context = context;
        this.onClose = onClose;
    }

    /** Returns the clipboard text, or "" when empty or when Android refuses the read. */
    @JavascriptInterface
    public String getClipboardText() {
        try {
            ClipboardManager manager =
                    (ClipboardManager) context.getSystemService(Context.CLIPBOARD_SERVICE);
            if (manager == null || !manager.hasPrimaryClip()) {
                return "";
            }
            ClipData data = manager.getPrimaryClip();
            if (data == null || data.getItemCount() == 0) {
                return "";
            }
            CharSequence text = data.getItemAt(0).coerceToText(context);
            return text == null ? "" : text.toString();
        } catch (Exception e) {
            return "";
        }
    }

    @JavascriptInterface
    public boolean copyText(String text) {
        try {
            ClipboardManager manager =
                    (ClipboardManager) context.getSystemService(Context.CLIPBOARD_SERVICE);
            if (manager == null) {
                return false;
            }
            manager.setPrimaryClip(ClipData.newPlainText("HAMO AI", text));
            return true;
        } catch (Exception e) {
            return false;
        }
    }

    @JavascriptInterface
    public void closePanel() {
        if (onClose != null) {
            main.post(onClose);
        }
    }
}
