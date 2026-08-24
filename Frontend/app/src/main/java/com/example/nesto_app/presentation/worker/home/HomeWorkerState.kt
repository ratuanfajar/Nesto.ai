package com.example.nesto_app.presentation.worker.home

import com.example.nesto_app.domain.entities.Project
import com.example.nesto_app.utils.State
import kotlin.time.ExperimentalTime
import kotlin.time.Instant

data class HomeWorkerState @OptIn(ExperimentalTime::class) constructor(
    val isRefreshing: Boolean = false,
    val searchName: String = "",
    val projects : State<List<Project>> = State.Loading()
)