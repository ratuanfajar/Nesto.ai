package com.example.nesto_app.data.remotes.sources

import android.content.Context
import com.example.nesto_app.R
import com.example.nesto_app.data.remotes.response.CutListResponse
import com.example.nesto_app.data.remotes.services.CutListService
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.serialization.json.Json
import okhttp3.MultipartBody
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class CutListRemoteDataSources @Inject constructor(
    private val cutListService: CutListService,
    @ApplicationContext private val context: Context
){
    private val jsonFormatter = Json {
        ignoreUnknownKeys = true
        isLenient = true
    }

//    suspend fun analyze(image: List<MultipartBody.Part>): CutListResponse {
//        val jsonString = context.resources
//            .openRawResource(R.raw.dummy)
//            .bufferedReader()
//            .use { it.readText() }
//
//        return jsonFormatter.decodeFromString<CutListResponse>(jsonString)
//    }

    suspend fun analyze(image: List<MultipartBody.Part>): CutListResponse {
        return cutListService.analyze(image)
    }
}