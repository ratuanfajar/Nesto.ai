package com.example.nesto_app.utils.exceptions

import org.json.JSONObject
import retrofit2.HttpException

fun HttpException.getErrorMessage(): String {
    val raw = response()?.errorBody()?.string()

    return try {
        val json = JSONObject(raw ?: "")
        json.getString("message")
    } catch (e: Exception) {
        message() ?: "Unknown error"
    }
}