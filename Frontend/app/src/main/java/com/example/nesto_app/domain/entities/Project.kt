package com.example.nesto_app.domain.entities

data class Project(
    val id: Int,
    val name: String,
    val listCutList: List<CutList>
)