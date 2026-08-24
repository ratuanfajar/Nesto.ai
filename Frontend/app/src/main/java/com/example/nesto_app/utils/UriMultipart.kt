package com.example.nesto_app.utils

import android.content.Context
import android.net.Uri
import android.webkit.MimeTypeMap
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import java.io.File

fun Uri.toMultipart(
    context: Context,
    partName: String,
    allowedMimeTypes: List<String>? = null
): MultipartBody.Part{
    val mimeType = context.contentResolver.getType(this) ?: "application/octet-stream"

    if (allowedMimeTypes != null && mimeType !in allowedMimeTypes) {
        throw IllegalArgumentException("Unsupported file type: $mimeType. Allowed: $allowedMimeTypes")
    }

    val extension = MimeTypeMap.getSingleton()
        .getExtensionFromMimeType(mimeType)
        ?.let { ".$it" }
        ?: ".tmp"

    val inputStream = context.contentResolver.openInputStream(this)
        ?: throw Exception("Cannot open file")

    val file = File.createTempFile("upload_",extension,context.cacheDir)

    inputStream.use {
            input ->
        file.outputStream().use {
                output ->
            input.copyTo(output)
        }
    }

    val requestBody = file.asRequestBody(mimeType.toMediaType())
    return MultipartBody.Part.createFormData(
        partName,
        file.name,
        requestBody
    )
}