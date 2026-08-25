package com.example.nesto_app.global.networks

import com.example.nesto_app.BuildConfig

object NetworkConstants {
    const val BASE_URL = BuildConfig.API_BASE_URL
    const val ANALYZE = "v1/analyze"
    const val HEADER_API_KEY = "X-API-KEY"
}