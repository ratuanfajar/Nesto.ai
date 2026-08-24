package com.example.nesto_app.presentation.worker.project.create_project

import android.net.Uri
import com.example.nesto_app.domain.entities.CutList


data class CreateProjectState(
    val selectedUris: List<Uri> = emptyList(),
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
    val cutList: CutList? = null
)
