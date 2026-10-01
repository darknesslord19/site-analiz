package com.example.domainpatch;

import android.content.Context;

public class DomainStore {
    public static Context app;
    static final String DEF = "https://www.hdfilmcehennemi.nl";

    public static String get(Context c) {
        return c.getSharedPreferences("domain_prefs", 0).getString("domain", DEF);
    }

    public static void set(Context c, String v) {
        c.getSharedPreferences("domain_prefs", 0).edit().putString("domain", v).apply();
    }

    public static String read() {
        return app == null ? DEF : get(app);
    }
}
