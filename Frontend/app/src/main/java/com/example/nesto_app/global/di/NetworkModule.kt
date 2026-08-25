package com.example.nesto_app.global.di

import android.content.Context
import android.content.SharedPreferences
import com.example.nesto_app.data.remotes.services.CutListService
import com.example.nesto_app.global.di.providers.ApiKeyInterceptor
import com.example.nesto_app.global.di.providers.ApiKeyProvider
import com.example.nesto_app.global.networks.NetworkConstants
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    @Provides
    @Singleton
    fun provideSharedPreferences(
        @ApplicationContext context: Context
    ): SharedPreferences {
        return context.getSharedPreferences("nesto_prefs", Context.MODE_PRIVATE)
    }

    @Provides
    @Singleton
    fun provideApiKeyProvider(
        sharedPreferences: SharedPreferences
    ): ApiKeyProvider {
        return ApiKeyProvider(sharedPreferences)
    }

    @Provides
    @Singleton
    fun provideApiKeyInterceptor(
        apiKeyProvider: ApiKeyProvider
    ): ApiKeyInterceptor {
        return ApiKeyInterceptor { apiKeyProvider.getApiKey() }
    }

    @Provides
    @Singleton
    fun provideLoggingInterceptor(): HttpLoggingInterceptor {
        return HttpLoggingInterceptor().setLevel(HttpLoggingInterceptor.Level.BODY)
    }

    @Provides
    @Singleton
    fun provideOkHttpClient(
        apiKeyInterceptor: ApiKeyInterceptor,
        loggingInterceptor: HttpLoggingInterceptor
    ): OkHttpClient {
        return OkHttpClient.Builder()
            .addInterceptor(apiKeyInterceptor)
            .addInterceptor(loggingInterceptor)
            .connectTimeout(120, TimeUnit.SECONDS)
            .readTimeout(120, TimeUnit.SECONDS)
            .build()
    }

    @Provides
    @Singleton
    fun provideRetrofit (
        okHttpClient: OkHttpClient
    ) : Retrofit {
        val json = Json{
            ignoreUnknownKeys = true
            coerceInputValues = true
            explicitNulls = false
        }
        return Retrofit.Builder()
            .client(okHttpClient)
            .baseUrl(NetworkConstants.BASE_URL)
            .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
            .build()
    }

    @Provides
    @Singleton
    fun provideCutListService(retrofit: Retrofit): CutListService{
        return retrofit.create<CutListService>(CutListService::class.java)
    }
}