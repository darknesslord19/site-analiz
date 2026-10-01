package com.example.domainpatch;

import android.app.Activity;
import android.app.Dialog;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.util.Base64;
import android.view.ViewGroup;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Scanner;
import org.json.JSONObject;

public class Hook {
    static final String RAW = "https://raw.githubusercontent.com/darknesslord19/site-analiz/main/domains.json";
    static final String TG = "https://t.me/darknes_lord";
    static final String TOKEN = "";
    static final String HTML = "PCFET0NUWVBFIGh0bWw+CjxodG1sIGxhbmc9InRyIj4KPGhlYWQ+CjxtZXRhIGNoYXJzZXQ9InV0Zi04Ij4KPG1ldGEgbmFtZT0idmlld3BvcnQiIGNvbnRlbnQ9IndpZHRoPWRldmljZS13aWR0aCwgaW5pdGlhbC1zY2FsZT0xIj4KPHRpdGxlPkRvbWFpbiBBeWFyxLE8L3RpdGxlPgo8c3R5bGU+CiAgOnJvb3R7LS1iZzojMTYyMjJjOy0tcGFuZWw6IzFlMmUzYjstLWluazojZWFmMWY0Oy0tbXV0ZTojOGZhNWIzOy0tbGluZTojMzI0OTVhOy0tYWNjZW50OiMyZmQwYjU7LS10ZzojMmFhM2UwOy0tZXJyOiNmZjdhN2E7Y29sb3Itc2NoZW1lOmRhcmt9CiAgQG1lZGlhIChwcmVmZXJzLWNvbG9yLXNjaGVtZTpsaWdodCl7OnJvb3R7LS1iZzojZWVmM2Y1Oy0tcGFuZWw6I2ZmZjstLWluazojMTQyMzJlOy0tbXV0ZTojNWQ3Njg2Oy0tbGluZTojY2RkYWUxOy0tYWNjZW50OiMwYzlhODU7LS10ZzojMWI4NmJkOy0tZXJyOiNjNjNhM2E7Y29sb3Itc2NoZW1lOmxpZ2h0fX0KICAqe2JveC1zaXppbmc6Ym9yZGVyLWJveH0KICBodG1sLGJvZHl7bWFyZ2luOjA7YmFja2dyb3VuZDp2YXIoLS1iZyk7Y29sb3I6dmFyKC0taW5rKTtmb250OjE2cHgvMS40NSBzeXN0ZW0tdWksc2Fucy1zZXJpZn0KICBtYWlue21heC13aWR0aDo0MjBweDttYXJnaW46MCBhdXRvO3BhZGRpbmc6MjBweCAxNnB4IDI4cHh9CiAgaDF7Zm9udC1zaXplOjEuMnJlbTttYXJnaW46MCAwIDRweH0KICBwLnN1YnttYXJnaW46MCAwIDE4cHg7Y29sb3I6dmFyKC0tbXV0ZSk7Zm9udC1zaXplOi45cmVtfQogIC5ib3h7YmFja2dyb3VuZDp2YXIoLS1wYW5lbCk7Ym9yZGVyOjFweCBzb2xpZCB2YXIoLS1saW5lKTtib3JkZXItcmFkaXVzOjEwcHg7cGFkZGluZzoxNHB4fQogIGxhYmVse2Rpc3BsYXk6YmxvY2s7Zm9udC1zaXplOi44NXJlbTtjb2xvcjp2YXIoLS1tdXRlKTttYXJnaW4tYm90dG9tOjZweH0KICAuY3Vye2ZvbnQ6Ljg1cmVtIHVpLW1vbm9zcGFjZSxtb25vc3BhY2U7d29yZC1icmVhazpicmVhay1hbGw7bWFyZ2luOjAgMCAxNHB4fQogIGlucHV0e3dpZHRoOjEwMCU7cGFkZGluZzoxMnB4O2JvcmRlci1yYWRpdXM6OHB4O2JvcmRlcjoxcHggc29saWQgdmFyKC0tbGluZSk7YmFja2dyb3VuZDp0cmFuc3BhcmVudDtjb2xvcjp2YXIoLS1pbmspO2ZvbnQ6aW5oZXJpdH0KICBpbnB1dDpmb2N1cy12aXNpYmxlLGJ1dHRvbjpmb2N1cy12aXNpYmxle291dGxpbmU6MnB4IHNvbGlkIHZhcigtLWFjY2VudCk7b3V0bGluZS1vZmZzZXQ6MnB4fQogIC5yb3d7ZGlzcGxheTpmbGV4O2dhcDoxMHB4O21hcmdpbi10b3A6MTJweH0KICBidXR0b257ZmxleDoxO3BhZGRpbmc6MTJweDtib3JkZXItcmFkaXVzOjhweDtib3JkZXI6MXB4IHNvbGlkIHZhcigtLWxpbmUpO2JhY2tncm91bmQ6dHJhbnNwYXJlbnQ7Y29sb3I6dmFyKC0taW5rKTtmb250OmluaGVyaXQ7Zm9udC13ZWlnaHQ6NjAwO2N1cnNvcjpwb2ludGVyfQogIGJ1dHRvbi5zYXZle2JhY2tncm91bmQ6dmFyKC0tYWNjZW50KTtib3JkZXItY29sb3I6dmFyKC0tYWNjZW50KTtjb2xvcjojMDYyNDFmfQogIGJ1dHRvbi50Z3t3aWR0aDoxMDAlO21hcmdpbi10b3A6MTJweDtib3JkZXItY29sb3I6dmFyKC0tdGcpO2NvbG9yOnZhcigtLXRnKX0KICBidXR0b246ZGlzYWJsZWR7b3BhY2l0eTouNX0KICAjbXNne21pbi1oZWlnaHQ6MS40ZW07bWFyZ2luOjEycHggMCAwO2ZvbnQtc2l6ZTouOXJlbX0KICAjbXNnLmVycntjb2xvcjp2YXIoLS1lcnIpfSAjbXNnLm9re2NvbG9yOnZhcigtLWFjY2VudCl9Cjwvc3R5bGU+CjwvaGVhZD4KPGJvZHk+CjxtYWluPgogIDxoMT5TaXRlIGFkcmVzaTwvaDE+CiAgPHAgY2xhc3M9InN1YiI+RWtsZW50aW5pbiBrdWxsYW5kxLHEn8SxIGRvbWFpbidpIGJ1cmFkYW4gZGXEn2nFn3RpcmViaWxpcnNpbi48L3A+CgogIDxkaXYgY2xhc3M9ImJveCI+CiAgICA8bGFiZWw+xZ51IGFua2kgYWRyZXM8L2xhYmVsPgogICAgPHAgY2xhc3M9ImN1ciIgaWQ9ImN1ciI+LTwvcD4KCiAgICA8bGFiZWwgZm9yPSJ1cmwiPlllbmkgYWRyZXM8L2xhYmVsPgogICAgPGlucHV0IGlkPSJ1cmwiIHR5cGU9InVybCIgaW5wdXRtb2RlPSJ1cmwiIGF1dG9jb21wbGV0ZT0ib2ZmIiBwbGFjZWhvbGRlcj0iaHR0cHM6Ly9vcm5lay5jb20iPgoKICAgIDxkaXYgY2xhc3M9InJvdyI+CiAgICAgIDxidXR0b24gaWQ9InB1bGwiIHR5cGU9ImJ1dHRvbiI+UmVwb2RhbiDDp2VrPC9idXR0b24+CiAgICAgIDxidXR0b24gaWQ9InNhdmUiIGNsYXNzPSJzYXZlIiB0eXBlPSJidXR0b24iPktheWRldDwvYnV0dG9uPgogICAgPC9kaXY+CiAgICA8cCBpZD0ibXNnIiByb2xlPSJzdGF0dXMiPjwvcD4KICA8L2Rpdj4KCiAgPGJ1dHRvbiBpZD0idGciIGNsYXNzPSJ0ZyIgdHlwZT0iYnV0dG9uIj5UZWxlZ3JhbTwvYnV0dG9uPgo8L21haW4+Cgo8c2NyaXB0Pgpjb25zdCAkID0gaWQgPT4gZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoaWQpOwpjb25zdCBtc2cgPSAodCwgYykgPT4geyAkKCdtc2cnKS50ZXh0Q29udGVudCA9IHQ7ICQoJ21zZycpLmNsYXNzTmFtZSA9IGMgfHwgJyc7IH07CgovLyBBbmRyb2lkIGvDtnByw7xzw7wgeW9rc2EgdGFyYXnEsWPEsWRhIHRlc3QgacOnaW4gc2FodGUgbmVzbmUKY29uc3QgQSA9IHdpbmRvdy5BbmRyb2lkIHx8IHsKICBnZXREb21haW46ICgpID0+IGxvY2FsU3RvcmFnZS5kIHx8ICdodHRwczovL29ybmVrLmNvbScsCiAgZmV0Y2hGcm9tUmVwbzogKCkgPT4gc2V0VGltZW91dCgoKSA9PiB3aW5kb3cub25GZXRjaGVkKCdodHRwczovL3llbmktb3JuZWsuY29tJywgJycpLCA1MDApLAogIHNhdmU6IHUgPT4geyBsb2NhbFN0b3JhZ2UuZCA9IHU7IH0sCiAgb3BlblRlbGVncmFtOiAoKSA9PiB3aW5kb3cub3BlbignaHR0cHM6Ly90Lm1lLycpCn07CgpmdW5jdGlvbiBzaG93KHUpeyAkKCdjdXInKS50ZXh0Q29udGVudCA9IHU7ICQoJ3VybCcpLnZhbHVlID0gdTsgfQpzaG93KEEuZ2V0RG9tYWluKCkpOwoKLy8gS290bGluIHRhcmFmxLEgYnUgZm9ua3NpeW9udSDDp2HEn8SxcsSxcgp3aW5kb3cub25GZXRjaGVkID0gKHVybCwgZXJyb3IpID0+IHsKICAkKCdwdWxsJykuZGlzYWJsZWQgPSBmYWxzZTsKICBpZiAoZXJyb3IpIHJldHVybiBtc2coZXJyb3IsICdlcnInKTsKICAkKCd1cmwnKS52YWx1ZSA9IHVybDsKICBtc2coJ1JlcG9kYW4gw6dla2lsZGkuIEtheWRldFwnZSBiYXNhcmFrIHV5Z3VsYS4nLCAnb2snKTsKfTsKCiQoJ3B1bGwnKS5vbmNsaWNrID0gKCkgPT4geyAkKCdwdWxsJykuZGlzYWJsZWQgPSB0cnVlOyBtc2coJ8OHZWtpbGl5b3IuLi4nKTsgQS5mZXRjaEZyb21SZXBvKCk7IH07CgokKCdzYXZlJykub25jbGljayA9ICgpID0+IHsKICBjb25zdCB1ID0gJCgndXJsJykudmFsdWUudHJpbSgpLnJlcGxhY2UoL1wvKyQvLCAnJyk7CiAgaWYgKCEvXmh0dHBzPzpcL1wvW15ccy9dK1wuW15ccy9dKy8udGVzdCh1KSkgcmV0dXJuIG1zZygnR2XDp2VybGkgYmlyIGFkcmVzIGdpciAoaHR0cHM6Ly8uLi4pLicsICdlcnInKTsKICBBLnNhdmUodSk7IHNob3codSk7IG1zZygnS2F5ZGVkaWxkaS4nLCAnb2snKTsKfTsKCiQoJ3RnJykub25jbGljayA9ICgpID0+IEEub3BlblRlbGVncmFtKCk7Cjwvc2NyaXB0Pgo8L2JvZHk+CjwvaHRtbD4K";

    public static void init(Object plugin, Context ctx) {
        try {
            DomainStore.app = ctx.getApplicationContext();
            Method setter = null;
            for (Method m : plugin.getClass().getMethods())
                if (m.getName().equals("setOpenSettings")) setter = m;
            if (setter == null) return;
            Class<?> fn = setter.getParameterTypes()[0];
            final Object unit = Class.forName("kotlin.Unit").getField("INSTANCE").get(null);
            Object proxy = Proxy.newProxyInstance(fn.getClassLoader(), new Class[]{fn}, new InvocationHandler() {
                public Object invoke(Object p, Method m, Object[] a) {
                    String n = m.getName();
                    if (n.equals("invoke")) {
                        if (a != null && a.length > 0 && a[0] instanceof Activity) show((Activity) a[0]);
                        return unit;
                    }
                    if (n.equals("hashCode")) return 0;
                    if (n.equals("equals")) return false;
                    return null;
                }
            });
            setter.invoke(plugin, proxy);
        } catch (Throwable t) { }
    }

    static void show(final Activity act) {
        act.runOnUiThread(new Runnable() {
            public void run() {
                Dialog d = new Dialog(act);
                WebView w = new WebView(act);
                w.getSettings().setJavaScriptEnabled(true);
                w.addJavascriptInterface(new Bridge(act, w), "Android");
                String html = new String(Base64.decode(HTML, Base64.DEFAULT), java.nio.charset.Charset.forName("UTF-8"));
                w.loadDataWithBaseURL(null, html, "text/html", "utf-8", null);
                d.setContentView(w);
                d.show();
                d.getWindow().setLayout(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT);
            }
        });
    }

    static class Bridge {
        final Activity act;
        final WebView web;
        Bridge(Activity a, WebView w) { act = a; web = w; }

        @JavascriptInterface public String getDomain() { return DomainStore.get(act); }
        @JavascriptInterface public void save(String u) { DomainStore.set(act, u); }
        @JavascriptInterface public void openTelegram() {
            act.startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(TG)));
        }
        @JavascriptInterface public void fetchFromRepo() {
            new Thread(new Runnable() {
                public void run() {
                    String url = "", err = "";
                    try {
                        HttpURLConnection c = (HttpURLConnection) new URL(RAW).openConnection();
                        if (TOKEN.length() > 0) c.setRequestProperty("Authorization", "token " + TOKEN);
                        c.setConnectTimeout(8000);
                        c.setReadTimeout(8000);
                        Scanner s = new Scanner(c.getInputStream(), "UTF-8").useDelimiter("\\A");
                        url = new JSONObject(s.hasNext() ? s.next() : "").getString("domain");
                    } catch (Exception e) { err = "Repo okunamadı: " + e.getMessage(); }
                    final String js = "onFetched(" + JSONObject.quote(url) + "," + JSONObject.quote(err) + ")";
                    act.runOnUiThread(new Runnable() {
                        public void run() { web.evaluateJavascript(js, null); }
                    });
                }
            }).start();
        }
    }
}
