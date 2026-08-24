package com.example.nesto_app.data.remotes.services

import com.example.nesto_app.data.remotes.response.CutListResponse
import com.example.nesto_app.global.networks.NetworkConstants
import okhttp3.MultipartBody
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part

interface CutListService {
    @Multipart
    @POST(NetworkConstants.ANALYZE)
    suspend fun analyze(
        @Part image: List<MultipartBody.Part>,
    ) : CutListResponse
}