package com.example.nesto_app.domain.entities

import kotlin.time.ExperimentalTime

data class CutList @OptIn(ExperimentalTime::class) constructor(
    val id:Int,
    val name: String
)