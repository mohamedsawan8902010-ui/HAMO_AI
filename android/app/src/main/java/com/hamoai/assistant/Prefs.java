package com.hamoai.assistant;

import android.content.Context;

/** Tiny settings store (private SharedPreferences). */
final class Prefs {
    static final String DEFAULT_URL = "http://127.0.0.1:8000/";
    private static final String FILE = "hamo_prefs";
    private static final String KEY_URL = "server_url";

    private Prefs() {}

    static String serverUrl(Context context) {
        String saved = context.getSharedPreferences(FILE, Context.MODE_PRIVATE)
                .getString(KEY_URL, DEFAULT_URL);
        return normalize(saved);
    }

    static void saveServerUrl(Context context, String url) {
        context.getSharedPreferences(FILE, Context.MODE_PRIVATE)
                .edit()
                .putString(KEY_URL, normalize(url))
                .apply();
    }

    static String normalize(String raw) {
        String url = raw == null ? "" : raw.trim();
        if (url.isEmpty()) {
            return DEFAULT_URL;
        }
        if (!url.startsWith("http://") && !url.startsWith("https://")) {
            url = "http://" + url;
        }
        if (!url.endsWith("/")) {
            url = url + "/";
        }
        return url;
    }
}
