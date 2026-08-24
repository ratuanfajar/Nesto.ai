package com.example.nesto_app.domain.repositories

import android.net.Uri
import com.example.nesto_app.domain.entities.CutList
import com.example.nesto_app.utils.State
import kotlinx.coroutines.flow.Flow

interface CutListRepository {
    suspend fun analyze(images : List<Uri>): Flow<State<CutList>>
}