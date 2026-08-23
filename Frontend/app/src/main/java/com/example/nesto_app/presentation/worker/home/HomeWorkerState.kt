package com.example.nesto_app.presentation.worker.home

import com.example.nesto_app.utils.State
import kotlin.time.ExperimentalTime
import kotlin.time.Instant

data class HomeWorkerState @OptIn(ExperimentalTime::class) constructor(
    val isRefreshing: Boolean = false,
    val cutlist : State<Order> = listOf()
)