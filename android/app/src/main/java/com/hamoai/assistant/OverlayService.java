package com.hamoai.assistant;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.graphics.PixelFormat;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.Icon;
import android.os.Build;
import android.os.IBinder;
import android.provider.Settings;
import android.util.DisplayMetrics;
import android.util.TypedValue;
import android.view.ContextThemeWrapper;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewConfiguration;
import android.view.ViewOutlineProvider;
import android.view.WindowManager;
import android.webkit.WebView;
import android.widget.FrameLayout;
import android.widget.TextView;
import android.widget.Toast;

/**
 * Foreground service that draws the floating "H" button over other apps (Chrome included).
 * Tap the button: the assistant panel (the same web UI) opens. Close it: you are back in the page.
 * Needs the "Display over other apps" permission (SYSTEM_ALERT_WINDOW).
 */
public class OverlayService extends Service {
    static final String ACTION_STOP = "com.hamoai.assistant.STOP";
    private static final String CHANNEL_ID = "hamo_overlay";
    private static final int NOTIFICATION_ID = 1001;

    private WindowManager windowManager;
    private TextView bubble;
    private WindowManager.LayoutParams bubbleParams;
    private FrameLayout panel;
    private WebView webView;

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && ACTION_STOP.equals(intent.getAction())) {
            stopSelf();
            return START_NOT_STICKY;
        }

        startAsForeground();

        if (!Settings.canDrawOverlays(this)) {
            Toast.makeText(this, "امنح HAMO AI إذن الظهور فوق التطبيقات أولًا", Toast.LENGTH_LONG).show();
            stopSelf();
            return START_NOT_STICKY;
        }

        windowManager = (WindowManager) getSystemService(WINDOW_SERVICE);
        if (bubble == null) {
            try {
                createBubble();
            } catch (Exception e) {
                Toast.makeText(this, "تعذر إظهار الزر العائم على هذا الجهاز", Toast.LENGTH_LONG).show();
                stopSelf();
            }
        }
        return START_NOT_STICKY;
    }

    private void startAsForeground() {
        NotificationManager manager = getSystemService(NotificationManager.class);
        manager.createNotificationChannel(
                new NotificationChannel(CHANNEL_ID, "HAMO AI", NotificationManager.IMPORTANCE_LOW));

        int piFlags = PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT;
        PendingIntent open = PendingIntent.getActivity(
                this, 0, new Intent(this, MainActivity.class), piFlags);
        Intent stopIntent = new Intent(this, OverlayService.class).setAction(ACTION_STOP);
        PendingIntent stop = PendingIntent.getService(this, 1, stopIntent, piFlags);

        Notification.Action stopAction = new Notification.Action.Builder(
                Icon.createWithResource(this, R.drawable.ic_stat_hamo), "إيقاف", stop).build();

        Notification notification = new Notification.Builder(this, CHANNEL_ID)
                .setSmallIcon(R.drawable.ic_stat_hamo)
                .setContentTitle("HAMO AI يعمل")
                .setContentText("اضغط الزر العائم H لفتح المساعد")
                .setContentIntent(open)
                .setOngoing(true)
                .addAction(stopAction)
                .build();

        if (Build.VERSION.SDK_INT >= 34) {
            startForeground(NOTIFICATION_ID, notification,
                    ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE);
        } else {
            startForeground(NOTIFICATION_ID, notification);
        }
    }

    private int dp(int value) {
        return (int) TypedValue.applyDimension(
                TypedValue.COMPLEX_UNIT_DIP, value, getResources().getDisplayMetrics());
    }

    // ---- floating button -------------------------------------------------------------------

    private void createBubble() {
        final int size = dp(56);
        DisplayMetrics screen = getResources().getDisplayMetrics();

        bubble = new TextView(this);
        bubble.setText("H");
        bubble.setTextColor(0xFFFFFFFF);
        bubble.setTextSize(TypedValue.COMPLEX_UNIT_SP, 24);
        bubble.setTypeface(Typeface.DEFAULT_BOLD);
        bubble.setGravity(Gravity.CENTER);
        GradientDrawable background = new GradientDrawable();
        background.setShape(GradientDrawable.OVAL);
        background.setColor(0xFF536DFE);
        background.setStroke(dp(2), 0x66FFFFFF);
        bubble.setBackground(background);
        bubble.setOnClickListener(v -> showPanel());
        bubble.setOnTouchListener(new DragListener(size));

        bubbleParams = new WindowManager.LayoutParams(
                size, size,
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
                        | WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
                PixelFormat.TRANSLUCENT);
        bubbleParams.gravity = Gravity.TOP | Gravity.LEFT;
        bubbleParams.x = screen.widthPixels - size - dp(8);
        bubbleParams.y = screen.heightPixels / 3;
        windowManager.addView(bubble, bubbleParams);
    }

    /** Drag the bubble anywhere; a short tap (no movement) opens the panel. */
    private final class DragListener implements View.OnTouchListener {
        private final int size;
        private final int slop = ViewConfiguration.get(OverlayService.this).getScaledTouchSlop();
        private float downX;
        private float downY;
        private int startX;
        private int startY;
        private boolean moved;

        DragListener(int size) {
            this.size = size;
        }

        @Override
        public boolean onTouch(View view, MotionEvent event) {
            switch (event.getActionMasked()) {
                case MotionEvent.ACTION_DOWN:
                    downX = event.getRawX();
                    downY = event.getRawY();
                    startX = bubbleParams.x;
                    startY = bubbleParams.y;
                    moved = false;
                    return true;
                case MotionEvent.ACTION_MOVE:
                    float dx = event.getRawX() - downX;
                    float dy = event.getRawY() - downY;
                    if (!moved && Math.hypot(dx, dy) > slop) {
                        moved = true;
                    }
                    if (moved) {
                        DisplayMetrics screen = getResources().getDisplayMetrics();
                        bubbleParams.x = clamp(startX + (int) dx, 0, screen.widthPixels - size);
                        bubbleParams.y = clamp(startY + (int) dy, 0, screen.heightPixels - size);
                        windowManager.updateViewLayout(bubble, bubbleParams);
                    }
                    return true;
                case MotionEvent.ACTION_UP:
                    if (!moved) {
                        view.performClick();
                    }
                    return true;
                default:
                    return false;
            }
        }
    }

    private static int clamp(int value, int min, int max) {
        return Math.max(min, Math.min(value, Math.max(min, max)));
    }

    // ---- assistant panel -------------------------------------------------------------------

    private void showPanel() {
        if (panel != null || windowManager == null) {
            return;
        }
        DisplayMetrics screen = getResources().getDisplayMetrics();
        ContextThemeWrapper themed = new ContextThemeWrapper(this, android.R.style.Theme_DeviceDefault);

        if (webView == null) {
            webView = HamoWebView.create(themed, Prefs.serverUrl(this), this::hidePanel);
        }
        webView.onResume();

        panel = new FrameLayout(themed) {
            @Override
            public boolean dispatchKeyEvent(KeyEvent event) {
                if (event.getKeyCode() == KeyEvent.KEYCODE_BACK
                        && event.getAction() == KeyEvent.ACTION_UP) {
                    hidePanel();
                    return true;
                }
                return super.dispatchKeyEvent(event);
            }
        };
        GradientDrawable background = new GradientDrawable();
        background.setColor(0xFF0D1220);
        background.setCornerRadius(dp(18));
        background.setStroke(dp(1), 0xFF26304A);
        panel.setBackground(background);
        panel.setClipToOutline(true);
        panel.setOutlineProvider(ViewOutlineProvider.BACKGROUND);
        panel.addView(webView, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT));

        int width = Math.min(screen.widthPixels - dp(16), dp(520));
        int height = (int) (screen.heightPixels * 0.55f);
        // No FLAG_NOT_FOCUSABLE: the panel needs the keyboard and the clipboard.
        // FLAG_NOT_TOUCH_MODAL: taps outside the panel still reach the page underneath.
        WindowManager.LayoutParams params = new WindowManager.LayoutParams(
                width, height,
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
                PixelFormat.TRANSLUCENT);
        params.gravity = Gravity.TOP | Gravity.CENTER_HORIZONTAL;
        params.y = dp(36);
        params.softInputMode = WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE;

        try {
            windowManager.addView(panel, params);
            bubble.setVisibility(View.GONE);
        } catch (Exception e) {
            panel.removeAllViews();
            panel = null;
            Toast.makeText(this, "تعذر فتح نافذة المساعد", Toast.LENGTH_LONG).show();
        }
    }

    private void hidePanel() {
        if (panel == null) {
            return;
        }
        try {
            windowManager.removeView(panel);
        } catch (Exception ignored) {
            // Already removed.
        }
        panel.removeAllViews();
        panel = null;
        if (webView != null) {
            webView.onPause();
        }
        if (bubble != null) {
            bubble.setVisibility(View.VISIBLE);
        }
    }

    @Override
    public void onDestroy() {
        hidePanel();
        if (bubble != null && windowManager != null) {
            try {
                windowManager.removeView(bubble);
            } catch (Exception ignored) {
                // Already removed.
            }
        }
        bubble = null;
        if (webView != null) {
            webView.destroy();
            webView = null;
        }
        super.onDestroy();
    }
}
