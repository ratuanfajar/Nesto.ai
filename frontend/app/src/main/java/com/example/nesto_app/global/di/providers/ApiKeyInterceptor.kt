package com.example.nesto_app.global.di.providers

import com.example.nesto_app.global.networks.NetworkConstants
import okhttp3.Interceptor
import okhttp3.Response

class ApiKeyInterceptor(
    private val apiKeyProvider: () -> String?
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val original = chain.request()
        val apiKey = apiKeyProvider()

        val request = if (!apiKey.isNullOrBlank()){
            original.newBuilder()
                .header(NetworkConstants.HEADER_API_KEY, apiKey)
                .build()
        } else{
            original
        }
        return chain.proceed(request)
    }
}