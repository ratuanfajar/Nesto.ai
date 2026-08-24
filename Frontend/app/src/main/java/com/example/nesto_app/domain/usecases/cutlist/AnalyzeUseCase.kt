package com.example.nesto_app.domain.usecases.cutlist

import android.net.Uri
import com.example.nesto_app.domain.entities.CutList
import com.example.nesto_app.domain.repositories.CutListRepository
import com.example.nesto_app.utils.State
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject

class AnalyzeUseCase @Inject constructor(
    private val cutListRepository: CutListRepository
) {
    suspend fun run(image: List<Uri>): Flow<State<CutList>> {
        return cutListRepository.analyze(image)
    }
}