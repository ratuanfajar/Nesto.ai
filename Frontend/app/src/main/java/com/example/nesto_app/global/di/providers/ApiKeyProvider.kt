package com.example.nesto_app.global.di.providers

import android.content.SharedPreferences
import com.example.nesto_app.BuildConfig

class ApiKeyProvider(
    private val prefs: SharedPreferences
) {
    companion object {
        private const val KEY_API_KEY = "nesto_api_key"
    }

    fun getApiKey(): String? {
        return prefs.getString(KEY_API_KEY, null)
            ?: BuildConfig.NESTO_API_KEY.takeIf { it.isNotBlank() }
    }

    fun setApiKey(value: String?){
        prefs.edit().putString(KEY_API_KEY, value?.takeIf { it.isNotBlank() }).apply()
    }
}