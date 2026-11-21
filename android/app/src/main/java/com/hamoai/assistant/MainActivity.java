package com.hamoai.assistant;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.util.TypedValue;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/** Control screen: permission, start/stop the floating button, server address, connection test. */
public class MainActivity extends Activity {
    private static final int BG = 0xFF0D1220;
    private static final int SURFACE = 0xFF151C2E;
    private static final int LINE = 0xFF26304A;
    private static final int BRAND = 0xFF536DFE;
    private static final int TEXT = 0xFFEEF1F8;
    private static final int MUTED = 0xFF9AA5BD;

    private TextView overlayStatus;
    private TextView serverStatus;
    private EditText urlInput;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().getDecorView().setLayoutDirection(View.LAYOUT_DIRECTION_RTL);

        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(BG);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(20), dp(32), dp(20), dp(32));
        scroll.addView(root, new ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        root.addView(text("HAMO AI", 30, TEXT, true));
        root.addView(text("مساعدك التعليمي فوق أي صفحة تدرس منها", 15, MUTED, false));

        overlayStatus = text("", 15, TEXT, false);
        serverStatus = text("", 15, TEXT, false);
        addSpace(root, 20);
        root.addView(overlayStatus);
        root.addView(serverStatus);

        addSpace(root, 8);
        root.addView(button("١) منح إذن الظهور فوق التطبيقات", false, v -> {
            Intent intent = new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    Uri.parse("package:" + getPackageName()));
            startActivity(intent);
        }));
        root.addView(button("٢) تشغيل الزر العائم", true, v -> startOverlay()));
        root.addView(button("إيقاف الزر العائم", false, v -> {
            stopService(new Intent(this, OverlayService.class));
            Toast.makeText(this, "تم إيقاف الزر العائم", Toast.LENGTH_SHORT).show();
        }));
        root.addView(button("فتح المحادثة داخل التطبيق", false,
                v -> startActivity(new Intent(this, ChatActivity.class))));
        root.addView(button("اختبار الاتصال بالخادم", false, v -> testConnection()));

        addSpace(root, 20);
        root.addView(text("عنوان الخادم", 14, MUTED, false));
        urlInput = new EditText(this);
        urlInput.setSingleLine(true);
        urlInput.setTextColor(TEXT);
        urlInput.setHintTextColor(MUTED);
        urlInput.setText(Prefs.serverUrl(this));
        urlInput.setLayoutDirection(View.LAYOUT_DIRECTION_LTR);
        root.addView(urlInput);
        root.addView(button("حفظ العنوان", false, v -> saveUrl()));

        addSpace(root, 20);
        root.addView(text(
                "قبل الاستخدام شغّل الخادم في Termux بالأمر:  bash start.sh\n"
                        + "ثم افتح Chrome واضغط الزر العائم H، والصق النص الذي تريد شرحه.",
                14, MUTED, false));

        setContentView(scroll);
    }

    @Override
    protected void onResume() {
        super.onResume();
        overlayStatus.setText("إذن الظهور فوق التطبيقات: "
                + (Settings.canDrawOverlays(this) ? "مفعّل ✔" : "غير مفعّل ✖"));
        testConnection();
    }

    private void startOverlay() {
        if (!Settings.canDrawOverlays(this)) {
            Toast.makeText(this, "امنح إذن الظهور فوق التطبيقات أولًا (الخطوة ١)",
                    Toast.LENGTH_LONG).show();
            return;
        }
        if (Build.VERSION.SDK_INT >= 33
                && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 1);
        }
        startForegroundService(new Intent(this, OverlayService.class));
        Toast.makeText(this, "تم التشغيل. افتح Chrome وستجد الزر H فوق الصفحة.",
                Toast.LENGTH_LONG).show();
    }

    private void saveUrl() {
        Prefs.saveServerUrl(this, urlInput.getText().toString());
        String saved = Prefs.serverUrl(this);
        urlInput.setText(saved);
        Uri uri = Uri.parse(saved);
        boolean local = "127.0.0.1".equals(uri.getHost()) || "localhost".equals(uri.getHost());
        if ("http".equals(uri.getScheme()) && !local) {
            Toast.makeText(this, "الاتصال غير المشفّر مسموح فقط لـ 127.0.0.1. استخدم https.",
                    Toast.LENGTH_LONG).show();
        } else {
            Toast.makeText(this, "تم الحفظ. أعد تشغيل الزر العائم ليطبّق العنوان.",
                    Toast.LENGTH_LONG).show();
        }
        testConnection();
    }

    private void testConnection() {
        serverStatus.setText("الخادم: جارٍ الفحص…");
        final String url = Prefs.serverUrl(this) + "health";
        new Thread(() -> {
            String result;
            try {
                HttpURLConnection connection = (HttpURLConnection) new URL(url).openConnection();
                connection.setConnectTimeout(3000);
                connection.setReadTimeout(3000);
                int code = connection.getResponseCode();
                StringBuilder body = new StringBuilder();
                if (code == 200) {
                    try (BufferedReader reader = new BufferedReader(new InputStreamReader(
                            connection.getInputStream(), StandardCharsets.UTF_8))) {
                        String line;
                        while ((line = reader.readLine()) != null) {
                            body.append(line);
                        }
                    }
                }
                connection.disconnect();
                result = code == 200 && body.toString().contains("\"ok\"")
                        ? "الخادم: يعمل ✔"
                        : "الخادم: استجابة غير متوقعة (" + code + ") ✖";
            } catch (Exception e) {
                result = "الخادم: غير متصل ✖ — شغّله في Termux";
            }
            final String message = result;
            runOnUiThread(() -> serverStatus.setText(message));
        }).start();
    }

    // ---- small view helpers ----------------------------------------------------------------

    private int dp(int value) {
        return (int) TypedValue.applyDimension(
                TypedValue.COMPLEX_UNIT_DIP, value, getResources().getDisplayMetrics());
    }

    private TextView text(String value, int sp, int color, boolean bold) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextColor(color);
        view.setTextSize(TypedValue.COMPLEX_UNIT_SP, sp);
        view.setLineSpacing(0, 1.3f);
        if (bold) {
            view.setTypeface(view.getTypeface(), android.graphics.Typeface.BOLD);
        }
        return view;
    }

    private void addSpace(LinearLayout parent, int heightDp) {
        View space = new View(this);
        parent.addView(space, new LinearLayout.LayoutParams(1, dp(heightDp)));
    }

    private Button button(String label, boolean primary, View.OnClickListener listener) {
        Button button = new Button(this);
        button.setText(label);
        button.setAllCaps(false);
        button.setTextColor(primary ? 0xFFFFFFFF : TEXT);
        button.setTextSize(TypedValue.COMPLEX_UNIT_SP, 15);
        GradientDrawable background = new GradientDrawable();
        background.setCornerRadius(dp(12));
        if (primary) {
            background.setColor(BRAND);
        } else {
            background.setColor(SURFACE);
            background.setStroke(dp(1), LINE);
        }
        button.setBackground(background);
        button.setOnClickListener(listener);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(50));
        params.topMargin = dp(10);
        button.setLayoutParams(params);
        return button;
    }
}
