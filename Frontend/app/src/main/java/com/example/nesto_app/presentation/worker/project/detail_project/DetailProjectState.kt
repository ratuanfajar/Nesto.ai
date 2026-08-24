package com.example.nesto_app.presentation.worker.project.detail_project

import com.example.nesto_app.domain.entities.Project
import com.example.nesto_app.utils.State
import kotlin.time.ExperimentalTime

data class DetailProjectState @OptIn(ExperimentalTime::class) constructor(
    val project : State<Project> = State.Loading()
)