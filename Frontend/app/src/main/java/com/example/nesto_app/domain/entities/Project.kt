package com.example.nesto_app.domain.entities

import kotlin.time.ExperimentalTime
import kotlin.time.Instant


data class Project @OptIn(ExperimentalTime::class) constructor(
    val id: Int,
    val name: String,
    val cutList: CutList,
    val createdAt: Instant
)